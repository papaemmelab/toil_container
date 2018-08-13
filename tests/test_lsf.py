"""toil_container jobs tests."""

import os
from past.utils import old_div

from toil.batchSystems.lsfHelper import parse_memory_limit
from toil.batchSystems.lsfHelper import parse_memory_resource
from toil.batchSystems.lsfHelper import per_core_reservation

from toil_container import parsers
from toil_container import jobs
from toil_container import lsf
from toil_container import utils

from .utils import Capturing
from .utils import SKIP_LSF


def test_encode_decode_resources():
    expected = {"runtime": 1}
    e_string = lsf._encode_dict(expected)
    obtained = lsf._decode_dict(e_string)
    assert lsf._encode_dict({}) == ""
    assert lsf._decode_dict("") == {}
    assert expected == obtained


def test_build_bsub_line():
    os.environ["TOIL_LSF_ARGS"] = "-q test"
    mem = 2147483648
    cpu = 1

    obtained = lsf.build_bsub_line(cpu=cpu, mem=mem, runtime=1, jobname='Test Job')

    if per_core_reservation():
        mem = float(mem) / 1024**3 / int(cpu)
    else:
        mem = old_div(float(mem), 1024**3)

    mem_resource = parse_memory_resource(mem)
    mem_limit = parse_memory_limit(mem)

    expected = [
        'bsub', '-cwd', '.', '-o', '/dev/null', '-e', '/dev/null',
        '-J', "'Test Job'", '-M', str(mem_limit), '-n', '1', '-W', '1',
        '-R', "'select[mem > {0} && type==X86_64] rusage[mem={0}]'".format(mem_resource),
        '-q', 'test']

    assert obtained == expected
    del os.environ["TOIL_LSF_ARGS"]


@SKIP_LSF
def test_bsubline_works():
    command = lsf.build_bsub_line(
        cpu=1,
        mem=2147483648,
        runtime=1,
        jobname='Test Job')

    command.extend(["-K", "echo"])
    assert utils.subprocess.check_call(command) == 0


@SKIP_LSF
def test_custom_lsf_batch_system(tmpdir):
    jobstore = tmpdir.join("jobstore").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore])
    options.batchSystem = "CustomLSF"
    job = jobs.ContainerJob(options, memory="10G", runtime=1)

    with Capturing() as output:
        jobs.ContainerJob.Runner.startToil(job, options)

    output = " ".join(output)
    assert "select[type==X86_64 && mem > 10]" in output
    assert "-W 1" in output
