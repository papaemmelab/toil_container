"""A custom Slurm batchsystem to process additional resources."""
# pylint: disable=C0103, W0223

import logging

from slugify import slugify
from toil import subprocess
from toil.batchSystems.slurm import SlurmBatchSystem

from toil_container.base import ToilContainerBaseBatchSystem

logger = logging.getLogger(__name__)


class CustomSlurmBatchSystem(ToilContainerBaseBatchSystem, SlurmBatchSystem):

    """Support runtime and resource based retries."""

    class Worker(ToilContainerBaseBatchSystem.Worker, SlurmBatchSystem.Worker):

        """Wrap sbatch command exporting the environment."""

        PENDING_STATES = {
            "PENDING",
            "RUNNING",
            "CONFIGURING",
            "COMPLETING",
            "RESIZING",
            "SUSPENDED",
        }

        def prepareSubmissionLine(self, cpu, mem, jobID, runtime, jobname):
            """Prepare custom qsub."""
            sbatch_line = super(CustomSlurmBatchSystem.Worker, self).prepareSbatch(
                cpu, mem, jobID
            )

            try:  # use our toil container job name
                sbatch_line[sbatch_line.index("-J") + 1] = jobname
            except (ValueError, IndexError):
                pass

            # redirect stdout and stderr to /dev/null
            sbatch_line += [
                "--output=/dev/null",
                "--error=/dev/null",
            ]

            if runtime:
                sbatch_line += ["--time={}".format(runtime)]

            return [i for i in sbatch_line if not (i.startswith("--mem=") or i == "-Q")]

        def getJobExitCode(self, batchJobID):
            logger.debug("Getting exit code for slurm job %d", int(batchJobID))

            state, rc = self._getJobDetailsFromSacct(batchJobID)

            if rc == -999:
                state, rc = self._getJobDetailsFromScontrol(batchJobID)

            logger.debug("s job state is %s", state)

            # If Job is in a running state, return None to indicate no update
            if state in self.PENDING_STATES:
                return None

            if state == "TIMEOUT":
                return "runlimit"

            if state == "OUT_OF_MEMORY":
                return "memlimit"

            return rc

        def prepareJobName(self, jobname):
            return slugify(jobname)

        def prepareCommand(self, command):
            return "--wrap={}".format(command)

        @staticmethod
        def getNotFinishedJobsIDs():
            # pending states supported by sacct
            return {
                int(i.split(".")[0])
                for i in subprocess.check_output(
                    [
                        "sacct",
                        "-s",
                        ",".join({"PENDING", "RUNNING", "RESIZING", "SUSPENDED"}),
                        "-P",
                        "-o",
                        "jobid",
                        "-S",
                        "1970-01-01",
                        "-n",
                    ]
                )
                .decode("utf-8")
                .strip()
                .split("\n")
                if i.split(".")[0].isdigit()
            }
