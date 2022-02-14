"""toil_container jobs tests."""

import os
import subprocess
import time

from toil.batchSystems.lsfHelper import parse_memory_limit
from toil.batchSystems.lsfHelper import parse_memory_resource
from toil.batchSystems.lsfHelper import per_core_reservation

from toil_container import parsers
from toil_container import jobs
from toil_container import lsf_helper

from .utils import SKIP_LSF


TEST_QUEUE = "general"


class testJobRuntimeRetry(jobs.ContainerJob):
    def run(self, fileStore):
        time.sleep(10)


def test_with_retries(tmpdir):
    test_path = tmpdir.join("test")

    def _test():
        if not os.path.isfile(test_path.strpath):
            test_path.write("hello")
            subprocess.check_call(["rm", "/florentino-ariza-volume"])
        return

    lsf_helper.with_retries(_test)


def test_encode_decode_resources():
    expected = {"runtime": 1}
    e_string = lsf_helper.encode_dict(expected)
    obtained = lsf_helper.decode_dict(e_string)
    assert lsf_helper.encode_dict({}) == ""
    assert lsf_helper.decode_dict("") == {}
    assert expected == obtained


@SKIP_LSF
def test_build_bsub_line():
    os.environ["TOIL_LSF_ARGS"] = f"-q {TEST_QUEUE}"
    mem = 2147483648
    cpu = 1

    obtained = lsf_helper.build_bsub_line(
        cpu=cpu, mem=mem, runtime=1, jobname="Test Job"
    )

    mem = float(mem) / 1024**3
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


@SKIP_LSF
def test_build_bsub_line_zero_cpus():
    lsf_helper.build_bsub_line(
        cpu=0,
        mem=2147483648,
        runtime=1,
        jobname="Test Job",
    )


@SKIP_LSF
def test_bsubline_works():
    command = lsf_helper.build_bsub_line(
        cpu=1, mem=2147483648, runtime=1, jobname="Test Job"
    )
    command.extend(["-K", "echo"])
    assert subprocess.check_call(command) == 0


@SKIP_LSF
def test_custom_lsf_batch_system(tmpdir):
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore, "--logFile", log])
    options.batchSystem = "custom_lsf"
    options.disableCaching = True
    job = jobs.ContainerJob(options, runtime=1)
    jobs.ContainerJob.Runner.startToil(job, options)

    with open(log, encoding="utf-8") as f:
        assert "-W 1" in f.read()


@SKIP_LSF
def test_custom_lsf_resource_retry_runtime(tmpdir):
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore, "--logFile", log])
    options.batchSystem = "custom_lsf"
    options.disableCaching = True
    job = testJobRuntimeRetry(options, runtime=1)
    testJobRuntimeRetry.Runner.startToil(job, options)

    with open(log, encoding="utf-8") as f:
        assert "Detected job killed by LSF" in f.read()


@SKIP_LSF
def test_custom_lsf_per_core_env(tmpdir):
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore, "--logFile", log])
    options.batchSystem = "custom_lsf"
    options.disableCaching = True

    # Set total memory per job
    os.environ["TOIL_CONTAINER_PER_CORE"] = "N"
    job_1 = jobs.ContainerJob(options, runtime=1, cores=2, memory="10G")
    jobs.ContainerJob.Runner.startToil(job_1, options)
    with open(log, "rt", encoding="utf-8") as f:
        assert "-M 10000MB -n 2" in f.read()

    # Set total memory per core
    os.environ["TOIL_CONTAINER_PER_CORE"] = "Y"
    job_2 = jobs.ContainerJob(options, runtime=1, cores=2, memory="10G")
    jobs.ContainerJob.Runner.startToil(job_2, options)
    with open(log, "rt", encoding="utf-8") as f:
        assert "-M 5000MB -n 2" in f.read()

    # Use per_core_reservation() from lsf config
    del os.environ["TOIL_CONTAINER_PER_CORE"]
    job_3 = jobs.ContainerJob(options, runtime=1, cores=2, memory="10G")
    jobs.ContainerJob.Runner.startToil(job_3, options)
    with open(log, "rt", encoding="utf-8") as f:
        assert (
            "-M 5000MB -n 2" if per_core_reservation() else "-M 10000MB -n 2"
        ) in f.read()


@SKIP_LSF
def test_custom_lsf_units_env(tmpdir):
    """Test environmental variable for setting LSF Default units."""
    jobstore = tmpdir.join("jobstore").strpath
    log = tmpdir.join("log.txt").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore, "--logFile", log])
    options.batchSystem = "custom_lsf"
    options.disableCaching = True
    options.logLevel = "debug"

    # Set lsf units as Gb
    os.environ["TOIL_CONTAINER_LSF_UNITS"] = "B"
    job_gb = testJobRuntimeRetry(options, memory="5Mb")
    jobs.ContainerJob.Runner.startToil(job_gb, options)
    with open(log, "rt", encoding="utf-8") as f:
        assert "-R select[mem>5MB] -R rusage[mem=5MB] -M 5MB" in f.read()

    # Set lsf units as Gb
    os.environ["TOIL_CONTAINER_LSF_UNITS"] = "Gb"
    job_gb = testJobRuntimeRetry(options, memory="2000Mb")
    jobs.ContainerJob.Runner.startToil(job_gb, options)
    with open(log, "rt", encoding="utf-8") as f:
        assert "-R select[mem>2000MB] -R rusage[mem=2000MB] -M 2000MB" in f.read()

    # Set lsf units as Mb
    os.environ["TOIL_CONTAINER_LSF_UNITS"] = "Mb"
    job_mb = jobs.ContainerJob(options, memory="2Mb")
    jobs.ContainerJob.Runner.startToil(job_mb, options)
    with open(log, "rt", encoding="utf-8") as f:
        assert "-R select[mem>2MB] -R rusage[mem=2MB] -M 2MB" in f.read()

    del os.environ["TOIL_CONTAINER_LSF_UNITS"]
