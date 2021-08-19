"""toil_container jobs tests."""

import os
import subprocess
import time

from toil.batchSystems.lsfHelper import parse_memory_limit
from toil.batchSystems.lsfHelper import parse_memory_resource
from toil.batchSystems.lsfHelper import per_core_reservation

from toil_container import parsers
from toil_container import jobs
from toil_container import lsf

from .utils import SKIP_LSF


TEST_QUEUE = "general"


class testJobRuntimeRetry(jobs.ContainerJob):
    def run(self, fileStore):
        time.sleep(70)


def test_with_retries(tmpdir):
    test_path = tmpdir.join("test")

    def _test():
        if not os.path.isfile(test_path.strpath):
            test_path.write("hello")
            subprocess.check_call(["rm", "/florentino-ariza-volume"])
        return

    lsf.with_retries(_test)


def test_encode_decode_resources():
    expected = {"runtime": 1}
    e_string = lsf._encode_dict(expected)
    obtained = lsf._decode_dict(e_string)
    assert lsf._encode_dict({}) == ""
    assert lsf._decode_dict("") == {}
    assert expected == obtained


def test_build_bsub_line():
    os.environ["TOIL_LSF_ARGS"] = f"-q {TEST_QUEUE}"
    mem = 2147483648
    cpu = 1

    obtained = lsf.build_bsub_line(cpu=cpu, mem=mem, runtime=1, jobname="Test Job")

    mem = float(mem) / 1024 ** 3
    if per_core_reservation():
        mem = mem / int(cpu or 1)

    mem_resource = parse_memory_resource(mem)
    mem_limit = parse_memory_limit(mem)

    expected = [
        "bsub",
        "-cwd",
        ".",
        "-o",
        "/dev/null",
        "-e",
        "/dev/null",
        "-J",
        "'Test Job'",
        "-R",
        "select[mem>{0}]".format(mem_resource),
        "-R",
        "rusage[mem={0}]".format(mem_resource),
        "-M",
        str(mem_limit),
        "-n",
        "1",
        "-W",
        "1",
        "-q",
        TEST_QUEUE,
    ]

    assert obtained == expected
    del os.environ["TOIL_LSF_ARGS"]


def test_build_bsub_line_zero_cpus():
    lsf.build_bsub_line(
        cpu=0,
        mem=2147483648,
        runtime=1,
        jobname="Test Job",
    )


@SKIP_LSF
def test_bsubline_works():
    command = lsf.build_bsub_line(cpu=1, mem=2147483648, runtime=1, jobname="Test Job")
    command.extend(["-K", "echo"])
    assert subprocess.check_call(command) == 0


@SKIP_LSF
def test_custom_lsf_batch_system(tmpdir):
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore, "--logFile", log])
    options.batchSystem = "custom_lsf"
    options.disableCaching = True
    job = jobs.ContainerJob(options, memory="10G", runtime=1)
    jobs.ContainerJob.Runner.startToil(job, options)

    with open(log) as f:
        assert "-W 1" in f.read()


@SKIP_LSF
def test_custom_lsf_resource_retry_runtime(tmpdir):
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore, "--logFile", log])
    options.batchSystem = "custom_lsf"
    options.disableCaching = True
    job = testJobRuntimeRetry(options, memory="10G", runtime=1)
    testJobRuntimeRetry.Runner.startToil(job, options)

    with open(log) as f:
        assert "Detected job killed by LSF" in f.read()
