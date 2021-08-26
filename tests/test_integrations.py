"""toil_container integration tests."""

from os.path import join

import pytest
from toil.leader import FailedJobsException

from toil_container import jobs
from toil_container import parsers
from toil_container.containers import _TMP_PREFIX
from .utils import DOCKER_IMAGE
from .utils import SINGULARITY_IMAGE
from .utils import SKIP_DOCKER
from .utils import SKIP_SINGULARITY


class ContainerTestJob(jobs.ContainerJob):

    """Test Job Class for Integration Test."""

    cmd = ["pwd"]
    cwd = None
    env = {}
    check_output = True

    def run(self, _):
        """Run job logic."""
        self.call(self.cmd, cwd=self.cwd, env=self.env, check_output=self.check_output)


def assert_pipeline(image_flag, image, tmpdir, parallel=True):
    """
    Make sure parallel jobs work.

                head
                |  |
          child_a  child_b
                |  |
                tail

    Make sure a failing job output is sent to the main pipeline logs

                head
                  |
               child_c
    """
    jobstore = tmpdir.join("jobstore")
    workdir = tmpdir.mkdir("working_dir")
    local_volume = tmpdir.mkdir("volume")
    container_volume = "/volume"

    # set parser
    parser = parsers.ContainerArgumentParser()
    args = [jobstore.strpath, "--workDir", workdir.strpath]

    if image_flag:
        args += [image_flag, image, "--volumes", local_volume.strpath, container_volume]

    # set testing variables
    out_file = "bottle.txt"
    tmp_file_local = workdir.join(out_file)
    tmp_file_container = join("/tmp", out_file)
    vol_file_local = local_volume.join(out_file)
    vol_file_container = join(container_volume, out_file)

    if image_flag is None:
        tmp_file_container = tmp_file_local.strpath
        vol_file_container = vol_file_local.strpath

    # create jobs
    options = parser.parse_args(args)

    if parallel:
        # Run the parallel pipeline
        head = ContainerTestJob(options)
        child_a = ContainerTestJob(options)
        child_b = ContainerTestJob(options)
        tail = ContainerTestJob(options)

        # assign commands and attributes
        cmd = ["/bin/bash", "-c"]

        # test cwd and workDir, _rm_tmp_dir is used to prevent tmpdir to be removed
        head._rm_tmp_dir = False
        head.cwd = "/bin"
        head.cmd = cmd + ["pwd >> " + tmp_file_container]

        # test env
        child_a.env = {"FOO": "BAR"}
        child_a.cmd = cmd + ["echo $FOO >> " + vol_file_container]

        # test check_output
        child_b.check_output = False
        child_b.cmd = cmd + ["echo check_call >> " + vol_file_container]

        # test volumes
        tail.cmd = cmd + ["echo volume >> " + vol_file_container]

        # build dag
        head.addChild(child_a)
        head.addChild(child_b)
        head.addFollowOn(tail)

        # start pipeline
        jobs.ContainerJob.Runner.startToil(head, options)

        if image_flag:
            pattern = join(_TMP_PREFIX + "*", out_file)
            tmp_file_local = next(workdir.visit(pattern))

        # Test the output
        with open(tmp_file_local.strpath) as f:
            result = f.read()
            assert "/bin" in result

        if image_flag:
            with open(vol_file_local.strpath) as f:
                result = f.read()
                assert "volume" in result
                assert "BAR" in result
                assert "check_call" in result

    else:
        # Run the failing pipeline
        options.retryCount = 0
        head = ContainerTestJob(options)
        child_c = ContainerTestJob(options)
        child_c.cmd = ["rm", "/florentino-arisa"]

        head.addChild(child_c)

        with pytest.raises(FailedJobsException) as captured_error:
            # start pipeline
            jobs.ContainerJob.Runner.startToil(head, options)

        assert (
            "rm: cannot remove '/florentino-arisa': No such file or directory"
        ) in captured_error.value.msg


def test_pipeline_with_subprocess(tmpdir):
    """Run the parallel pipeline."""
    assert_pipeline(None, None, tmpdir)


def test_failing_pipeline_with_subprocess(tmpdir):
    """Run the failing pipeline."""
    assert_pipeline(None, None, tmpdir, False)


@SKIP_DOCKER
def test_pipeline_with_docker(tmpdir):
    assert_pipeline("--docker", DOCKER_IMAGE, tmpdir)


@SKIP_SINGULARITY
def test_pipeline_with_singularity(tmpdir):
    assert_pipeline("--singularity", SINGULARITY_IMAGE, tmpdir)
