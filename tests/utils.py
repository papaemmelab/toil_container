"""toil_container tests utils."""

from cStringIO import StringIO
from os.path import abspath
from os.path import dirname
from os.path import join
import os
import sys
import time

import pytest

from toil_container import jobs
from toil_container import parsers
from toil_container import utils


ROOT = abspath(join(dirname(__file__), ".."))
DOCKER_IMAGE = "ubuntu:latest"
SKIP_LSF = pytest.mark.skipif(not utils.which("bsub"), reason="bsub is not available.")
SKIP_SGE = pytest.mark.skipif(not utils.which("qsub"), reason="qsub is not available.")
SKIP_SLURM = pytest.mark.skipif(
    not utils.which("sbatch"), reason="sbatch is not available."
)
SKIP_DOCKER = pytest.mark.skipif(
    not utils.is_docker_available(), reason="docker is not available."
)
SKIP_SINGULARITY = pytest.mark.skipif(
    not utils.is_singularity_available(), reason="singularity is not available."
)

if os.path.isfile(os.getenv("CACHED_SINGULARITY_IMAGE", "/")):
    SINGULARITY_IMAGE = os.getenv("CACHED_SINGULARITY_IMAGE")
else:
    SINGULARITY_IMAGE = "docker://" + DOCKER_IMAGE


class Capturing(list):

    """
    Capture stdout and stderr of a function call.

    See: https://stackoverflow.com/questions/16571150

    Example:

        with Capturing() as output:
            do_something(my_object)
    """

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


class TMPisPassed(jobs.ContainerJob):
    def run(self, fileStore):
        fileStore.logToMaster("TMP was: " + os.getenv("TMP"))


class JobRuntimeRetry(jobs.ContainerJob):
    def run(self, fileStore):
        time.sleep(70)


def check_env_and_runtime(tmpdir, batch_system, runtime_flag):
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args(
        [
            "--setEnv",
            "TMP=/tmp/ernest",
            "--logLevel",
            "debug",
            jobstore,
            "--logFile",
            log,
        ]
    )
    options.batchSystem = batch_system
    job = TMPisPassed(options, memory="10G", runtime=1)
    jobs.ContainerJob.Runner.startToil(job, options)

    with open(log) as f:
        content = f.read()

        # test runtime is passed
        assert runtime_flag in content

        # assert
        assert "TMP was: /tmp/ernest" in content


def retry_runtime(tmpdir, batch_system):
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore, "--logFile", log])
    options.batchSystem = batch_system
    job = JobRuntimeRetry(options, memory="10G", runtime=1)
    JobRuntimeRetry.Runner.startToil(job, options)

    with open(log) as f:
        assert "Job killed by scheduler" in f.read()
