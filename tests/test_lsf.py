"""toil_container jobs tests."""

import os

from toil_container import parsers
from toil_container import jobs
from toil_container import lsf
from toil_container import utils

from .utils import Capturing
from .utils import SKIP_LSF


def test_encode_decode_resources():
    expected = {"runtime": 1, "internet": True}
    e_string = lsf._encode_dict(expected)
    obtained = lsf._decode_dict(e_string)
    assert lsf._encode_dict({}) == ""
    assert lsf._decode_dict("") == {}
    assert expected == obtained


def test_build_bsub_line():
    os.environ["TOIL_LSF_ARGS"] = "-q test"
    obtained = lsf.build_bsub_line(
        cpu=1,
        mem=2147483648,
        internet=True,
        runtime=1,
        jobname='Test Job',
        )

    expected = [
        'bsub', '-cwd', '.', '-o', '/dev/null', '-e', '/dev/null',
        '-J', "'Test Job'", '-M', '2', '-n', '1', '-We', '1',
        '-R', "'select[mem > 2 && type==X86_64 && internet] rusage[iounits=0.2 && mem=2]'",
        '-q', 'test',
        ]

    assert obtained == expected
    del os.environ["TOIL_LSF_ARGS"]


@SKIP_LSF
def test_bsubline_works():
    command = lsf.build_bsub_line(
        cpu=1,
        mem=2147483648,
        internet=True,
        runtime=1,
        jobname='Test Job',
        )

    command.extend(["-K", "echo"])
    assert utils.subprocess.check_call(command) == 0


@SKIP_LSF
def test_custom_lsf_batch_system(tmpdir):
    jobstore = tmpdir.join("jobstore").strpath
    options = parsers.ToilBaseArgumentParser().parse_args([jobstore])
    options.batchSystem = "CustomLSF"
    job = jobs.ContainerJob(options, memory="10G", runtime=1, internet=True)

    with Capturing() as output:
        jobs.ContainerJob.Runner.startToil(job, options)

    output = " ".join(output)
    assert "select[type==X86_64 && mem > 10 && internet]" in output
    assert "-We 1" in output
