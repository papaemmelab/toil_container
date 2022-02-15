"""
Adapted from toil.batchSystems.lsfHelper.

https://github.com/DataBiosphere/toil/blob/master/src/toil/batchSystems/lsfHelper.py.
"""
import base64
import json
import os
import random
import subprocess
import time

from toil.lib.conversions import convert_units
from toil.batchSystems.lsf import logger
from toil.batchSystems.lsfHelper import per_core_reservation


_RESOURCES_START_TAG = "__rsrc"
_RESOURCES_CLOSE_TAG = "rsrc__"

try:
    MAX_MEMORY = int(os.getenv("TOIL_CONTAINER_RETRY_MEM", "60")) * 1e9
    MAX_RUNTIME = int(os.getenv("TOIL_CONTAINER_RETRY_RUNTIME", "40000"))
except ValueError:  # pragma: no cover
    MAX_MEMORY = 60 * 1e9
    MAX_RUNTIME = 40000
    logger.error("Failed to parse default values for resource retry.")


def _parse_memory(mem: float) -> str:
    """Parse memory parameter."""
    megabytes_of_mem = max(
        convert_units(
            float(mem),
            src_unit="B",  # Expect always bytes in `memory=<int>` if no explicit unit.
            dst_unit="MB",
        ),
        1.0,
    )
    # round as a string here to avoid returning something like 1.231e+12
    return f"{megabytes_of_mem:.0f}MB"


def encode_dict(dictionary):
    """Encode `dictionary` in string."""
    if dictionary:
        return (
            f"{_RESOURCES_START_TAG}"
            f"{base64.b64encode(json.dumps(dictionary).encode()).decode()}"
            f"{_RESOURCES_CLOSE_TAG}"
        )
    return ""


def decode_dict(string):
    """Get dictionary encoded in `string` by `encode_dict`."""
    if isinstance(string, str):
        split = string.split(_RESOURCES_START_TAG, 1)[-1]
        split = split.split(_RESOURCES_CLOSE_TAG, 1)
        if len(split) == 2:
            return json.loads(base64.b64decode(split[0]))
    return {}


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


def build_bsub_line(cpu, mem, runtime, jobname, stdoutfile=None, stderrfile=None):
    """
    Build an args list for a bsub submission.

    Arguments:
        cpu (int): number of cores needed.
        mem (float): number of bytes of memory needed.
        runtime (int): estimated run time for the job in minutes.
        jobname (str): the job name.
        stdoutfile (str): filename to direct job stdout
        stderrfile (str): filename to direct job stderr

    Returns:
        list: bsub command.
    """
    bsubline = [
        "bsub",
        "-cwd",
        ".",
        "-o",
        stdoutfile or "/dev/null",
        "-e",
        stderrfile or "/dev/null",
        "-J",
        f"'{jobname}'",
    ]
    cpu = int(cpu) or 1
    if mem:
        per_core = os.getenv("TOIL_CONTAINER_LSF_PER_CORE")
        if (per_core == "Y") or (not per_core and per_core_reservation()):
            mem = mem / cpu

        mem_resource = _parse_memory(mem)
        mem_limit = _parse_memory(mem)

        bsubline += ["-R", f"select[mem>{mem_resource}]"]
        bsubline += ["-R", f"rusage[mem={mem_resource}]"]
        bsubline += ["-M", str(mem_limit)]

    if cpu:
        bsubline += ["-n", str(cpu)]

    if runtime:
        bsubline += [os.getenv("TOIL_CONTAINER_RUNTIME_FLAG", "-W"), str(int(runtime))]

    if os.getenv("TOIL_LSF_ARGS"):
        bsubline.extend(os.getenv("TOIL_LSF_ARGS").split())

    # log to lsf
    logger.info("Submitting to LSF with: %s", " ".join(bsubline))
    return bsubline
