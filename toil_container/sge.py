"""A custom LSF batchsystem to process additional resources."""
# pylint: disable=C0103, W0223

from datetime import datetime
from pipes import quote
import logging
import math
import os

from past.utils import old_div
from slugify import slugify
from toil import subprocess
from toil.batchSystems import registry
from toil.batchSystems.gridengine import GridEngineBatchSystem

from .lsf import _MAX_MEMORY
from .lsf import _MAX_RUNTIME
from .lsf import _decode_dict
from .lsf import with_retries

logger = logging.getLogger(__name__)


class CustomSGEBatchSystem(GridEngineBatchSystem):

    """A custom SGE batchsystem used to encode extra lsf resources."""

    def __init__(self, config, maxCores, maxMemory, maxDisk):
        """Create a mapping table for JobIDs to JobNodes."""
        super(CustomSGEBatchSystem, self).__init__(config, maxCores, maxMemory, maxDisk)

        # will implement retry functionality later
        self.Id2Node = dict()
        self.resourceRetryCount = set()

        # toil has a bug where it uses maxLocalJobs to determine the number of threads
        # big mistake, as it results in thousands of worker threads being forked
        self.localBatch = registry.batchSystemFactoryFor(
            registry.defaultBatchSystem()
        )()(config, 1, maxMemory, maxDisk)

    def issueBatchJob(self, jobNode):
        """Load the JobNode into the JobID mapping table."""
        jobID = super(CustomSGEBatchSystem, self).issueBatchJob(jobNode)
        self.Id2Node[jobID] = jobNode
        return jobID

    class Worker(GridEngineBatchSystem.Worker):

        """Query running jobs more efficiently."""

        def forgetJob(self, jobID):
            """Remove jobNode from the mapping table when forgetting."""
            self.boss.Id2Node.pop(jobID, None)
            self.boss.resourceRetryCount.discard(jobID, None)
            return super(CustomSGEBatchSystem.Worker, self).forgetJob(jobID)

        def prepareQsub(self, cpu, mem, jobID, runtime=None):
            """Prepare custom qsub."""
            env_jobname = os.getenv("TOIL_LSF_JOBNAME", "toil-job")

            try:  # try to update runtime if not provided
                jobNode = self.boss.Id2Node[jobID]
                runtime = runtime or _decode_dict(jobNode.unitName).get("runtime", None)
                jobname = "{} {} {}".format(env_jobname, jobNode.jobName, jobID)
            except KeyError:
                jobname = "{} {}".format(env_jobname, jobID)

            qsubline = [
                "qsub",
                "-V",
                "-b",
                "y",
                "-terse",
                "-j",
                "y",
                "-cwd",
                "-N",
                slugify(jobname),
                # redirect stdout and stderr to /dev/null
                "-o",
                "/dev/null",
                "-e",
                "/dev/null",
            ]

            if runtime:
                qsubline += os.getenv(
                    "TOIL_CONTAINER_RUNTIME_FLAG", "-l h_rt"
                ).split() + ["00:{}:00".format(runtime)]

            if self.boss.environment:
                qsubline.append("-v")
                qsubline.append(
                    ",".join(
                        k + "=" + quote(os.environ[k] if v is None else v)
                        for k, v in self.boss.environment.items()
                    )
                )

            reqline = list()
            sgeArgs = os.getenv("TOIL_GRIDENGINE_ARGS")

            if mem is not None:
                # TODO: consider request an extra 25 % of memory for jobss
                # mem = mem * 1.25
                memStr = str(old_div(mem, 1024)) + "K"

                # for UGE instead of SGE; see #2309
                if not self.boss.config.manualMemArgs:
                    # reqline += ["vf=" + memStr, "h_vmem=" + memStr]
                    # TODO: dont kill jobs for memory until retry is implemented
                    reqline += ["vf=" + memStr]

                elif self.boss.config.manualMemArgs and not sgeArgs:
                    raise ValueError(
                        "--manualMemArgs set to True, but TOIL_GRIDGENGINE_ARGS is "
                        "not set. Please set TOIL_GRIDGENGINE_ARGS to specify memory "
                        "allocation for your system. Default adds the arguments: "
                        "vf=<mem> h_vmem=<mem> to qsub."
                    )

            if reqline:
                qsubline.extend(["-hard", "-l", ",".join(reqline)])

            if sgeArgs:
                sgeArgs = sgeArgs.split()
                for arg in sgeArgs:
                    if arg.startswith(("vf=", "hvmem=", "-pe")):
                        raise ValueError(
                            "Unexpected CPU, memory or pe specifications in "
                            " TOIL_GRIDGENGINE_ARGs: %s" % arg
                        )
                qsubline.extend(sgeArgs)

            if cpu is not None and math.ceil(cpu) > 1:
                peConfig = os.getenv("TOIL_GRIDENGINE_PE") or "shm"
                qsubline.extend(["-pe", peConfig, str(int(math.ceil(cpu)))])

            return qsubline

        def checkOnJobs(self):
            """
            Check and update status of all running jobs.

            Respects statePollingWait and will return cached results if not within
            time period to talk with the scheduler.
            """
            if (
                self._checkOnJobsTimestamp
                and (datetime.now() - self._checkOnJobsTimestamp).total_seconds()
                < self.boss.config.statePollingWait
            ):
                return self._checkOnJobsCache

            activity = False
            finished = with_retries(self._getDoneIDs)
            not_finished = with_retries(self._getNotFinishedIDs)

            for jobID in list(self.runningJobs):
                status = None
                batchJobID = self.getBatchSystemID(jobID)

                if batchJobID in not_finished:
                    logger.debug("Detected unfinished job %s", batchJobID)
                elif batchJobID in finished:
                    status = 0
                else:
                    status = with_retries(self.customGetJobExitCode, batchJobID, jobID)

                if status is not None:
                    activity = True
                    self.updatedJobsQueue.put((jobID, status))
                    self.forgetJob(jobID)

            self._checkOnJobsCache = activity
            self._checkOnJobsTimestamp = datetime.now()
            return activity

        def customGetJobExitCode(self, sgeID, jobID):
            """Get SGE exit code."""
            # the task is set as part of the job ID if using getBatchSystemID()
            if "." in sgeID:
                sgeID, task = sgeID.split(".", 1)

            command = ["qacct", "-j", str(sgeID)]

            if task is not None:
                command += ["-t", str(task)]

            killed = "qmaster enforced h_rt, h_cpu, or h_vmem limit"
            logger.debug("Checking job via: %s", " ".join(command))
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )

            for line in process.stdout:
                if line.startswith("failed") and killed in line:
                    return self._customRetry(jobID)
                elif line.startswith("failed") and int(line.split()[1]) == 1:
                    logger.debug("Exit Status: 1")
                    return 1
                elif line.startswith("exit_status"):
                    logger.debug("Exit Status: %r", line.split()[1])
                    return int(line.split()[1])

            logger.debug("Can't determine status for job: %s", sgeID)
            return None

        def _customRetry(self, jobID):
            """Retry job if killed by SGE due to runtime or memlimit problems."""
            try:
                jobNode = self.boss.Id2Node[jobID]
            except KeyError:
                logger.error("Can't resource retry %s, jobNode not found", jobID)
                return 1

            memory = _MAX_MEMORY
            runtime = _MAX_RUNTIME
            jobNode.jobName = (jobNode.jobName or "") + "-retry-memlimit-runlimit"
            qsub_line = self.prepareQsub(jobNode.cores, memory, jobID, runtime)

            if jobID not in self.boss.resourceRetryCount:
                sgeID = self.submitJob(qsub_line + [jobNode.command])
                self.batchJobIDs[jobID] = (sgeID, None)
                self.boss.resourceRetryCount.add(jobID)
                logger.info("Detected job killed by SGE, attempting retry: %s", sgeID)
            else:
                logger.error("Can't retry twice for: %s", jobID)
                return 1

            return None

        @staticmethod
        def _getNotFinishedIDs():
            return {
                int(i.split()[0])
                for i in subprocess.check_output(["qstat"])
                .decode("utf-8")
                .strip()
                .split("\n")[2:]
            }

        @staticmethod
        def _getDoneIDs():
            return {
                int(i.split()[0])
                for i in subprocess.check_output(["qstat", "-s", "z"])
                .decode("utf-8")
                .strip()
                .split("\n")[2:]
            }
