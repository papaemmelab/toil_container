"""A custom LSF batchsystem to process additional resources."""
# pylint: disable=C0103, W0223

import logging
import os

from past.utils import old_div
from toil import subprocess
from toil.batchSystems.lsf import LSFBatchSystem
from toil.batchSystems.lsfHelper import parse_memory_limit
from toil.batchSystems.lsfHelper import parse_memory_resource
from toil.batchSystems.lsfHelper import per_core_reservation

from toil_container.base import ToilContainerBaseBatchSystem

logger = logging.getLogger(__name__)


class CustomLSFBatchSystem(ToilContainerBaseBatchSystem, LSFBatchSystem):

    """Support runtime and resource based retries."""

    class Worker(ToilContainerBaseBatchSystem.Worker, LSFBatchSystem.Worker):

        _CANT_DETERMINE_JOB_STATUS = "NO STATUS FOUND"

        def prepareSubmissionLine(self, cpu, mem, jobID, runtime, jobname):
            """Make a bsub commandline to execute."""
            return build_bsub_line(cpu=cpu, mem=mem, runtime=runtime, jobname=jobname,)

        def getJobExitCode(self, batchJobID):
            """Get LSF exit code."""
            # the task is set as part of the job ID if using getBatchSystemID()
            if "." in batchJobID:
                batchJobID, _ = batchJobID.split(".", 1)

            commands = [
                ["bjobs", "-l", str(batchJobID)],
                ["bacct", "-l", str(batchJobID)],
                ["bhist", "-l", "-n", "1", str(batchJobID)],
                ["bhist", "-l", "-n", "2", str(batchJobID)],
            ]

            for i in commands:
                logger.debug("Checking job via: %s", " ".join(i))
                status = self._processStatusCommandLSF(i)

                if status != self._CANT_DETERMINE_JOB_STATUS:
                    return status

            logger.debug("Can't determine status for job: %s", batchJobID)
            return None

        def _processStatusCommandLSF(self, command):
            output = subprocess.check_output(command).decode("utf-8")
            cmdstr = " ".join(command)

            if "Done successfully" in output:
                logger.debug("Detected completed job: %s", cmdstr)
                status = 0

            elif "Completed <done>" in output:
                logger.debug("Detected completed job: %s", cmdstr)
                status = 0

            elif "TERM_MEMLIMIT" in output:
                status = "memlimit"

            elif "TERM_RUNLIMIT" in output:
                status = "runlimit"

            elif "New job is waiting for scheduling" in output:
                logger.debug("Detected job pending scheduling: %s", cmdstr)
                status = None

            elif "PENDING REASONS" in output:
                logger.debug("Detected pending job: %s", cmdstr)
                status = None

            elif "Started on " in output:
                logger.debug("Detected job started but not completed: %s", cmdstr)
                status = None

            elif "Completed <exit>" in output:
                logger.error("Detected failed job: %s", cmdstr)
                status = 1

            elif "Exited with exit code" in output:
                logger.error("Detected failed job: %s", cmdstr)
                status = 1

            else:
                status = self._CANT_DETERMINE_JOB_STATUS

            return status

        @staticmethod
        def getNotFinishedJobsIDs():
            return {
                int(i)
                for i in subprocess.check_output(["bjobs", "-o", "id"])
                .decode("utf-8")
                .strip()
                .split("\n")[1:]
            }


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

    cpu = int(cpu) or 1

    if mem:
        if os.getenv("TOIL_CONTAINER_PER_SLOT") == "Y" or per_core_reservation():
            mem = float(mem) / 1024 ** 3 / cpu
        else:
            mem = old_div(float(mem), 1024 ** 3)

        mem = mem if mem >= 1 else 1.0
        mem_resource = parse_memory_resource(mem)
        mem_limit = parse_memory_limit(mem)
        select.append("mem > {}".format(mem_resource))
        rusage.append("mem={}".format(mem_resource))
        bsubline += ["-M", str(mem_limit)]

    if cpu:
        bsubline += ["-n", str(cpu)]

    if runtime:
        bsubline += [os.getenv("TOIL_CONTAINER_RUNTIME_FLAG", "-W"), str(int(runtime))]

    if select:
        bsubline += ["-R", "select[%s]" % " && ".join(unique(select))]

    if rusage:
        bsubline += ["-R", "rusage[%s]" % " && ".join(unique(rusage))]

    if os.getenv("TOIL_LSF_ARGS"):
        bsubline.extend(os.getenv("TOIL_LSF_ARGS").split())

    # log to lsf
    logger.info("Submitting to LSF with: %s", " ".join(bsubline))
    return bsubline
