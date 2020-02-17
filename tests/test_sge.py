"""toil_container jobs tests."""

import os
import time

from toil_container import parsers
from toil_container import jobs

from .utils import Capturing
from .utils import SKIP_SGE


class testTMPisPassed(jobs.ContainerJob):
    def run(self, fileStore):
        fileStore.logToMaster("TMP was: " + os.getenv("TMP"))


class testJobRuntimeRetry(jobs.ContainerJob):
    def run(self, fileStore):
        time.sleep(70)


@SKIP_SGE
def test_custom_sge_batch_system(tmpdir):
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args(["--setEnv", "TMP=/tmp/ernest", "--logLevel", "debug", jobstore, "--logFile", log])
    options.batchSystem = "CustomSGE"
    job = testTMPisPassed(options, memory="10G", runtime=1)
    jobs.ContainerJob.Runner.startToil(job, options)

    with open(log) as f:
        content = f.read()
        
        # test runtime is passed
        assert "h_rt=00:1:00" in content
        
        # assert
        assert "TMP was: /tmp/ernest" in content
        


@SKIP_SGE
def test_custom_sge_resource_retry_runtime(tmpdir):
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore, "--logFile", log])
    options.batchSystem = "CustomSGE"
    job = testJobRuntimeRetry(options, memory="10G", runtime=1)
    testJobRuntimeRetry.Runner.startToil(job, options)

    with open(log) as f:
        assert "Detected job killed by SGE" in f.read()
