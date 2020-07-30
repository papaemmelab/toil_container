"""A custom LSF batchsystem to process additional resources."""
# pylint: disable=C0103, W0223

from collections import defaultdict
from collections import OrderedDict
from datetime import datetime
import base64
import json
import logging
import os
import random
import time

from toil import subprocess
from toil.batchSystems.abstractGridEngineBatchSystem import (
    AbstractGridEngineBatchSystem,
)

logger = logging.getLogger(__name__)

_RESOURCES_START_TAG = "__rsrc"
_RESOURCES_CLOSE_TAG = "rsrc__"
_PER_SLOT_LSF_CONFIG = "TOIL_CONTAINER_PER_SLOT"

try:
    _MAX_MEMORY = int(os.getenv("TOIL_CONTAINER_RETRY_MEM", 60)) * 1e9
    _MAX_RUNTIME = int(os.getenv("TOIL_CONTAINER_RETRY_RUNTIME", 40000))
except ValueError:  # pragma: no cover
    _MAX_MEMORY = 60 * 1e9
    _MAX_RUNTIME = 40000
    logger.error("Failed to parse default values for resource retry.")


def with_retries(operation, *args, **kwargs):
    """Add a random sleep after each retry."""
    latest_err = Exception

    for i in [2, 3, 5, 10]:
        try:
            return operation(*args, **kwargs)
        except subprocess.CalledProcessError as err:
            time.sleep(i + random.uniform(-i, i))
            latest_err = err
            logger.error(
                "Operation %s failed with code %d: %s",
                operation,
                err.returncode,
                err.output,
            )

    raise latest_err  # pragma: no cover


class ToilContainerBaseBatchSystem(AbstractGridEngineBatchSystem):

    """A custom base batchsystem used to encode extra resources."""

    def __init__(self, *args, **kwargs):
        """Create a mapping table for JobIDs to JobNodes."""
        super(ToilContainerBaseBatchSystem, self).__init__(*args, **kwargs)
        self.Id2Node = dict()
        self.resourceRetryCount = defaultdict(set)
        self.startTimeOrderedDict = OrderedDict()

    def issueBatchJob(self, jobNode):
        """Load the JobNode into the JobID mapping table."""
        jobID = super(ToilContainerBaseBatchSystem, self).issueBatchJob(jobNode)
        self.Id2Node[jobID] = jobNode
        self.startTimeOrderedDict[jobID] = datetime.now()
        return jobID

    class Worker(AbstractGridEngineBatchSystem.Worker):

        """Help parsing unitName and keeping track of resource retries."""

        # To be implemented by Custom Batch System
        # ----------------------------------------

        def __init__(self, *args, **kwargs):
            """Create a mapping table for JobIDs to JobNodes."""
            super(ToilContainerBaseBatchSystem.Worker, self).__init__(*args, **kwargs)
            self._LastActivityCount = -5

        @staticmethod
        def getNotFinishedJobsIDs():
            """Return set of jobs that are still not finished."""
            raise NotImplementedError

        def prepareSubmissionLine(self, cpu, mem, jobID, runtime, jobname):
            """Return sbatch, qsub, bsub line taking into account the runtime."""
            raise NotImplementedError

        def getCompletedJobsIDs(self):
            """Return set of jobs that have been completed."""
            return {}

        # Optional implementations by Custom Batch Systems
        # ------------------------------------------------

        def prepareCommand(self, command):
            """Optionally format the original toil command (i.e. path to executable)."""
            return command

        def prepareJobName(self, jobname):
            return jobname

        # Toil Container specific implementations and methods
        # ---------------------------------------------------

        def prepareSubmission(self, cpu, memory, jobID, command):
            unitname = getattr(self.boss.Id2Node.get(jobID), "unitName", "")
            runtime = _decode_dict(unitname).get("runtime", None)
            command = [self.prepareCommand(command)]
            jobname = self.prepareJobName(
                "{} {} {}".format(
                    os.getenv("TOIL_CONTAINER_JOBNAME", "Toil Job"),
                    getattr(self.boss.Id2Node.get(jobID), "jobName", ""),
                    jobID,
                )
            )

            return (
                self.prepareSubmissionLine(cpu, memory, jobID, runtime, jobname)
                + command
            )

        def resourceRetry(self, jobID, retry_type):
            """Retry job if killed by LSF due to runtime or memlimit problems."""
            try:
                jobNode = self.boss.Id2Node[jobID]
            except KeyError:
                logger.error("Can't resource retry %s, jobNode not found", jobID)
                return 1

            term_memlimit = retry_type in {"memlimit", "anylimit"}
            term_runlimit = retry_type in {"runlimit", "anylimit"}
            jobname = (jobNode.jobName or "") + "-resource-retry-" + retry_type
            memory = _MAX_MEMORY if term_memlimit else jobNode.memory
            runtime = _MAX_RUNTIME if term_runlimit else None
            command = self.prepareSubmissionLine(
                jobNode.cores, memory, jobID, runtime, self.prepareJobName(jobname)
            ) + [self.prepareCommand(jobNode.command)]

            if retry_type not in self.boss.resourceRetryCount[jobID]:
                batchID = self.submitJob(command)
                self.batchJobIDs[jobID] = (batchID, None)
                self.boss.resourceRetryCount[jobID].add(retry_type)
                logger.info("Job killed by scheduler, attempting retry: %s", batchID)
            else:
                logger.error("Can't retry for %s twice: %s", retry_type, jobID)
                return 1

            return None

        def forgetJob(self, jobID):
            """Remove jobNode from the mapping table when forgetting."""
            self.boss.Id2Node.pop(jobID, None)
            self.boss.resourceRetryCount.pop(jobID, None)
            self.boss.startTimeOrderedDict.pop(jobID, None)
            return super(ToilContainerBaseBatchSystem.Worker, self).forgetJob(jobID)

        def checkOnJobs(self):
            """
            Check and update status of all running jobs.

            Respects statePollingWait and will return cached results if not within
            time period to talk with the scheduler.
            """
            # ignore self.boss.config.statePollingWait
            polling_wait = min(60, 2 ** (self._LastActivityCount / 10))

            if (
                (datetime.now() - self._checkOnJobsTimestamp).total_seconds()
                < polling_wait
                if self._checkOnJobsTimestamp
                else False
            ):
                return self._checkOnJobsCache

            logger.info("Last polling wait time was: %s", polling_wait)
            activity = False
            not_finished = with_retries(self.getNotFinishedJobsIDs)
            completed = with_retries(self.getCompletedJobsIDs)
            self._LastActivityCount += 1

            for jobID in list(self.runningJobs):
                batchJobID = self.getBatchSystemID(jobID)
                status = None

                if int(batchJobID) in not_finished:
                    logger.debug("Detected unfinished job %s", batchJobID)
                elif int(batchJobID) in completed:
                    self._LastActivityCount = -5
                    status = 0
                else:
                    status = with_retries(self.getJobExitCode, batchJobID)

                    if status in {"runlimit", "memlimit", "anylimit"}:
                        status = self.resourceRetry(jobID, status)
                        self._LastActivityCount = -5

                if status is not None:
                    activity = True
                    self.updatedJobsQueue.put((jobID, status))
                    self.forgetJob(jobID)
                    logger.debug("Detected finished job %s", batchJobID)

            self._checkOnJobsCache = activity
            self._checkOnJobsTimestamp = datetime.now()
            return activity


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
