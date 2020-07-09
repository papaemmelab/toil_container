"""Toil Container LSF jobs tests."""

import os
from past.utils import old_div

from toil import subprocess
from toil.batchSystems.lsfHelper import parse_memory_limit
from toil.batchSystems.lsfHelper import parse_memory_resource
from toil.batchSystems.lsfHelper import per_core_reservation

from toil_container import lsf

from . import utils


def test_build_bsub_line():
    os.environ["TOIL_LSF_ARGS"] = "-q test"
    mem = 2147483648
    cpu = 1

    obtained = lsf.build_bsub_line(cpu=cpu, mem=mem, runtime=1, jobname="Test Job")

    if per_core_reservation():
        mem = float(mem) / 1024 ** 3 / int(cpu or 1)
    else:
        mem = old_div(float(mem), 1024 ** 3)

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
        "-M",
        str(mem_limit),
        "-n",
        "1",
        "-W",
        "1",
        "-R",
        "select[mem > {0}]".format(mem_resource),
        "-R",
        "rusage[mem={0}]".format(mem_resource),
        "-q",
        "test",
    ]

    assert obtained == expected
    del os.environ["TOIL_LSF_ARGS"]


def test_build_bsub_line_zero_cpus():
    lsf.build_bsub_line(cpu=0, mem=2147483648, runtime=1, jobname="Test Job")


@utils.SKIP_LSF
def test_bsubline_works():
    command = lsf.build_bsub_line(cpu=1, mem=2147483648, runtime=1, jobname="Test Job")
    command.extend(["-K", "echo"])
    assert subprocess.check_call(command) == 0


@utils.SKIP_SGE
def test_custom_lsf_batch_system(tmpdir):
    utils.check_env_and_runtime(tmpdir, "CustomLSF", "-W 1")


@utils.SKIP_SGE
def test_custom_lsf_resource_retry_runtime(tmpdir):
    utils.retry_runtime(tmpdir, "CustomLSF")
