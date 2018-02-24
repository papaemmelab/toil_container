"""toil_container integration tests."""

from os.path import join

from toil_container import jobs
from toil_container import parsers

from .utils import SKIP_DOCKER
from .utils import SKIP_SINGULARITY
from .utils import DOCKER_IMAGE
from .utils import SINGULARITY_IMAGE


class ContainerTestJob(jobs.ContainerJob):

    cmd = ["pwd"]
    cwd = None
    env = {}
    check_output = True

    def run(self, jobStore):
        self.call(
            self.cmd,
            cwd=self.cwd,
            env=self.env,
            check_output=self.check_output
            )


def assert_pipeline(image_flag, image, tmpdir):
    """
    Make sure parallel jobs work.

                head
                |  |
          child_a  child_b
                |  |
                tail
    """
    jobstore = tmpdir.join("jobstore")
    workdir = tmpdir.mkdir("working_dir")
    local_volume = tmpdir.mkdir("volume")
    container_volume = "/volume"

    # set parser
    parser = parsers.ContainerArgumentParser()
    args = [jobstore.strpath, "--workDir", workdir.strpath]

    if image_flag:
        args += [
            image_flag, image,
            "--volumes", local_volume.strpath, container_volume,
            ]

    # set testing variables
    out_file = "bottle.txt"
    tmp_file_workdir = workdir.join(out_file)
    tmp_file_container = join("/tmp", out_file)
    vol_file_local = local_volume.join(out_file)
    vol_file_container = join(container_volume, out_file)

    if image_flag and "singularity" in image_flag:
        tmp_file_workdir = workdir.join("scratch", "tmp", out_file)
    elif image_flag is None:
        tmp_file_container = tmp_file_workdir.strpath
        vol_file_container = vol_file_local.strpath

    # create jobs
    options = parser.parse_args(args)
    head = ContainerTestJob(options)
    child_a = ContainerTestJob(options)
    child_b = ContainerTestJob(options)
    tail = ContainerTestJob(options)

    # assign commands and attributes
    cmd = ["/bin/bash", "-c"]

    # test cwd
    head.cwd = "/bin"
    head.cmd = cmd + ["pwd >> " + tmp_file_container]

    # test env
    child_a.env = {"FOO": "BAR"}
    child_a.cmd = cmd + ["echo $FOO >> " + tmp_file_container]

    # test check_output
    child_b.check_output = False
    child_b.cmd = cmd + ["echo check_call >> " + tmp_file_container]

    # test volumes
    tail.cmd = cmd + ["echo volume >> " + vol_file_container]

    # build dag
    head.addChild(child_a)
    head.addChild(child_b)
    head.addFollowOn(tail)

    # start pipeline
    jobs.ContainerJob.Runner.startToil(head, options)

    # Test the output
    with open(tmp_file_workdir.strpath) as f:
        result = f.read()
        assert "/bin" in result
        assert "BAR" in result
        assert "check_call" in result

    if image_flag:
        with open(vol_file_local.strpath) as f:
            result = f.read()
            assert "volume" in result


def test_pipeline_with_subprocess(tmpdir):
    assert_pipeline(None, None, tmpdir)


@SKIP_DOCKER
def test_pipeline_with_docker(tmpdir):
    assert_pipeline("--docker", DOCKER_IMAGE, tmpdir)


@SKIP_SINGULARITY
def test_pipeline_with_singularity(tmpdir):
    assert_pipeline("--singularity", SINGULARITY_IMAGE, tmpdir)
