"""A custom LSF batchsystem to process additional resources."""
# pylint: disable=C0103, W0223

from datetime import datetime
import base64
import json
import logging
import os
import subprocess

from past.utils import old_div
from toil.batchSystems.abstractGridEngineBatchSystem import with_retries
from toil.batchSystems.lsf import LSFBatchSystem
from toil.batchSystems.lsfHelper import parse_memory_limit
from toil.batchSystems.lsfHelper import parse_memory_resource
from toil.batchSystems.lsfHelper import per_core_reservation

logger = logging.getLogger(__name__)

_RESOURCES_START_TAG = "__rsrc"
_RESOURCES_CLOSE_TAG = "rsrc__"
_PER_SLOT_LSF_CONFIG = "TOIL_CONTAINER_PER_SLOT"


class CustomLSFBatchSystem(LSFBatchSystem):

    """A custom LSF batchsystem used to encode extra lsf resources."""

    def __init__(self, *args, **kwargs):
        """Create a mapping table for JobIDs to JobNodes."""
        super(CustomLSFBatchSystem, self).__init__(*args, **kwargs)
        self.Id2Node = dict()
        self.customRetryCount = set()

    def issueBatchJob(self, jobNode):
        """Load the JobNode into the JobID mapping table."""
        jobID = super(CustomLSFBatchSystem, self).issueBatchJob(jobNode)
        self.Id2Node[jobID] = jobNode
        return jobID

    class Worker(LSFBatchSystem.Worker):

        """Make prepareBsub a class method and parse unitName."""

        _CANT_DETERMINE_JOB_STATUS = "NO STATUS FOUND"

        def forgetJob(self, jobID):
            """Remove jobNode from the mapping table when forgetting."""
            self.boss.Id2Node.pop(jobID, None)
            self.boss.customRetryCount.discard(jobID)
            return super(CustomLSFBatchSystem.Worker, self).forgetJob(jobID)

        def getNotFinishedIDs(self):
            return {
                int(i)
                for i in subprocess.check_output(["bjobs", "-o", "id"])
                .decode("utf-8")
                .strip()
                .split("\n")[1:]
            }

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
            not_finished = with_retries(self.getNotFinishedIDs)

            for jobID in list(self.runningJobs):
                batchJobID = self.getBatchSystemID(jobID)

                if batchJobID in not_finished:
                    logger.debug("bjobs detected unfinished job %s", batchJobID)
                else:
                    status = with_retries(self.customGetJobExitCode, batchJobID, jobID)
                    if status is not None:
                        activity = True
                        self.updatedJobsQueue.put((jobID, status))
                        self.forgetJob(jobID)

            self._checkOnJobsCache = activity
            self._checkOnJobsTimestamp = datetime.now()
            return activity

        def customGetJobExitCode(self, lsfID, jobID):
            # the task is set as part of the job ID if using getBatchSystemID()
            if "." in lsfID:
                lsfID, _ = lsfID.split(".", 1)

            commands = [
                ["bjobs", "-l", str(lsfID)],
                ["bacct", "-l", str(lsfID)],
                ["bhist", "-l", "-n", "1", str(lsfID)],
                ["bhist", "-l", "-n", "2", str(lsfID)],
            ]

            for i in commands:
                logger.debug("Checking job via: %s", " ".join(i))
                status = self._processStatusCommandLSF(i, jobID)

                if status != self._CANT_DETERMINE_JOB_STATUS:
                    return status

            logger.debug("Can't determine status for job: %s", lsfID)
            return None

        def _processStatusCommandLSF(self, command, jobID):
            output = subprocess.check_output(command)
            cmdstr = " ".join(command)

            if "Done successfully" in output:
                logger.debug("Detected completed job: %s", cmdstr)
                return 0

            elif "Completed <done>" in output:
                logger.debug("Detected completed job: %s", cmdstr)
                return 0

            elif "TERM_MEMLIMIT" in output:
                return with_retries(self.customRetry, jobID, term_memlimit=True)

            elif "TERM_RUNLIMIT" in output:
                return with_retries(self.customRetry, jobID, term_runlimit=True)

            elif "New job is waiting for scheduling" in output:
                logger.debug("Detected job pending scheduling: %s", cmdstr)
                return None

            elif "PENDING REASONS" in output:
                logger.debug("Detected pending job: %s", cmdstr)
                return None

            elif "Started on " in output:
                logger.debug("Detected job started but not completed: %s", cmdstr)
                return None

            elif "Completed <exit>" in output:
                logger.error("Detected failed job: %s", cmdstr)
                return 1

            elif "Exited with exit code" in output:
                logger.error("Detected failed job: %s", cmdstr)
                return 1

            return self._CANT_DETERMINE_JOB_STATUS

        def customRetry(self, jobID, term_memlimit=False, term_runlimit=False):
            """Retry job if killed by LSF due to runtime or memlimit problems."""
            if jobID in self.boss.customRetryCount:
                return 1

            self.boss.customRetryCount.add(jobID)
            jobNode = self.boss.Id2Node[jobID]
            jobNode.jobName = (jobNode.jobName or "") + " resource retry"
            max_memory = os.getenv("TOIL_CONTAINER_MAXMEM", "60G")
            max_runtime = os.getenv("TOIL_CONTAINER_MAXRUNTIME", 40000)
            memory = max_memory if term_memlimit else jobNode.memory
            runtime = max_runtime if term_runlimit else None
            bsub_line = self.prepareBsub(jobNode.cpu, memory, jobID, runtime)
            lsfID = self.submitJob(bsub_line + [jobNode.command])
            self.batchJobIDs[jobID] = (lsfID, None)
            logger.error("Detected job killed by LSF, attempting retry: %s", lsfID)

        def prepareBsub(self, cpu, mem, jobID, runtime=None):  # pylint: disable=W0221
            """
            Make a bsub commandline to execute.

            Arguments:
                cpu (int): number of cores needed.
                mem (float): number of bytes of memory needed.
                jobID (str): ID number of the job.
                runtime (int): total runtime.

            Returns:
                list: a bsub line argument.
            """
            jobNode = self.boss.Id2Node[jobID]
            resources = _decode_dict(jobNode.unitName)
            return build_bsub_line(
                cpu=cpu,
                mem=mem,
                runtime=runtime or resources.get("runtime"),
                jobname="{} {} {}".format(
                    os.getenv("TOIL_LSF_JOBNAME", "Toil Job"),
                    jobNode.jobName,
                    jobID,
                ),
            )


def build_bsub_line(cpu, mem, runtime, jobname):
    """
    Build an args list for a bsub submission.

    Arguments:
        cpu (int): number of cores needed.
        mem (float): number of bytes of memory needed.
        runtime (int): estimated run time for the job in minutes.
        jobname (str): the job name.

    Returns:
        list: bsub command.
    """
    unique = lambda i: sorted(set(map(str, i)))
    rusage = []
    select = []
    bsubline = [
        "bsub",
        "-cwd",
        ".",
        "-o",
        "/dev/null",
        "-e",
        "/dev/null",
        "-J",
        "'{}'".format(jobname),
    ]

    if mem:
        if os.getenv(_PER_SLOT_LSF_CONFIG) == "Y" or per_core_reservation():
            mem = float(mem) / 1024 ** 3 / int(cpu)
        else:
            mem = old_div(float(mem), 1024 ** 3)

        mem = mem if mem >= 1 else 1.0
        mem_resource = parse_memory_resource(mem)
        mem_limit = parse_memory_limit(mem)
        select.append("mem > {}".format(mem_resource))
        rusage.append("mem={}".format(mem_resource))
        bsubline += ["-M", str(mem_limit)]

    if cpu:
        bsubline += ["-n", str(int(cpu))]

    if runtime:
        bsubline += ["-W", str(int(runtime))]

    if select:
        bsubline += ["-R", "select[%s]" % " && ".join(unique(select))]

    if rusage:
        bsubline += ["-R", "rusage[%s]" % " && ".join(unique(rusage))]

    if os.getenv("TOIL_LSF_ARGS"):
        bsubline.extend(os.getenv("TOIL_LSF_ARGS").split())

    # log to lsf
    logger.info("Submitting to LSF with: %s", " ".join(bsubline))
    return bsubline


def _encode_dict(dictionary):
    """Encode `dictionary` in string."""
    if dictionary:
        return "{}{}{}".format(
            _RESOURCES_START_TAG,
            base64.b64encode(json.dumps(dictionary).encode()).decode(),
            _RESOURCES_CLOSE_TAG,
        )

    return ""


def _decode_dict(string):
    """Get dictionary encoded in `string` by `_encode_dict`."""
    if isinstance(string, str):
        split = string.split(_RESOURCES_START_TAG, 1)[-1]
        split = split.split(_RESOURCES_CLOSE_TAG, 1)

        if len(split) == 2:
            return json.loads(base64.b64decode(split[0]))

    return dict()
