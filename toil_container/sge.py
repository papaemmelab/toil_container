"""A custom SGE batchsystem to process additional resources."""
# pylint: disable=C0103, W0223, arguments-differ

from os.path import join
from uuid import uuid4
import logging
import os

from slugify import slugify
from toil import subprocess
from toil.batchSystems.gridengine import GridEngineBatchSystem

from toil_container.base import ToilContainerBaseBatchSystem

logger = logging.getLogger(__name__)


class CustomSGEBatchSystem(ToilContainerBaseBatchSystem, GridEngineBatchSystem):

    """Support runtime and resource based retries."""

    class Worker(ToilContainerBaseBatchSystem.Worker, GridEngineBatchSystem.Worker):

        """Wrap qsub command exporting the environment."""

        def prepareSubmissionLine(self, cpu, mem, jobID, runtime, jobname):
            """Prepare custom qsub."""
            qsubline = super(CustomSGEBatchSystem.Worker, self).prepareQsub(
                cpu, mem, jobID
            )

            try:  # use our toil container job name
                qsubline[qsubline.index("-N") + 1] = jobname
            except (ValueError, IndexError):
                pass

            # redirect stdout and stderr to /dev/null
            qsubline += [
                "-o",
                "/dev/null",
                "-e",
                "/dev/null",
            ]

            if runtime:
                qsubline += (
                    os.getenv("TOIL_CONTAINER_RUNTIME_FLAG", "-l h_rt")
                    + "=00:{}:00".format(runtime)
                ).split()

            # temporarily remove the memory hard limit
            return [i for i in qsubline if not i.startswith("h_vmem")]

        def getJobExitCode(self, batchJobID):
            """Get SGE exit code."""
            # the task is set as part of the job ID if using getBatchSystemID()
            task = None

            if "." in batchJobID:
                batchJobID, task = batchJobID.split(".", 1)

            command = ["qacct", "-j", str(batchJobID)]

            if task is not None:
                command += ["-t", str(task)]

            killed_string = "qmaster enforced h_rt, h_cpu, or h_vmem limit"
            logger.debug("Checking job via: %s", " ".join(command))
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )

            for line in process.stdout:
                if line.startswith("failed") and killed_string in line:
                    return "anylimit"  # tell toil container to retry with max resources
                elif line.startswith("failed") and int(line.split()[1]) == 1:
                    logger.debug("Exit Status: 1")
                    return 1
                elif line.startswith("exit_status"):
                    logger.debug("Exit Status: %r", line.split()[1])
                    return int(line.split()[1])

            logger.debug("Can't determine status for job: %s", batchJobID)
            return None

        def prepareJobName(self, jobname):
            return slugify(jobname)

        def prepareCommand(self, command):
            """Force exporting of environment variables in command script."""
            jobstore, jobdir = command.split("file:", 1)[1].split()
            command_dir = join(jobstore, "tmp", jobdir)
            subprocess.check_call("mkdir -p " + command_dir, shell=True)
            new_command = join(command_dir, str(uuid4()))

            # SGE overwrites TMP and TMPDIR! So annoying
            env = "\n".join(
                "export {}={}".format(*i) for i in self.boss.environment.items()
            )

            with open(new_command, "w+") as f:
                f.write("#!/bin/bash\n{}\n{}".format(env, command))

            os.chmod(new_command, 0o777)
            return new_command

        @staticmethod
        def getNotFinishedJobsIDs():
            return {
                int(i.split()[0])
                for i in subprocess.check_output(["qstat"])
                .decode("utf-8")
                .strip()
                .split("\n")[2:]
            }
