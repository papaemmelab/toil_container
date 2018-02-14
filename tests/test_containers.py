"""toil_container containers tests."""

from os.path import join
from os.path import abspath
from os.path import dirname
import os
import argparse
import subprocess

from docker.errors import ImageNotFound
import docker
import pytest

from toil.common import Toil
from toil.job import Job

from toil_container import __version__
from toil_container import utils
from toil_container.containers import Container
from toil_container.jobs import ContainerCallJob


ROOT = abspath(join(dirname(__file__), ".."))


def build_docker_image(image_tag):
    """Build image from Dockerfile if not created yet."""
    try:
        client = docker.from_env()
        client.images.get(image_tag)
    except ImageNotFound:
        client.images.build(path=ROOT, rm=True, tag=image_tag)


@pytest.mark.skipif(
    not utils.is_docker_available(),
    reason="docker is not available."
    )
def test_docker_container():
    """
    Test the docker image is created properly and it executes the entrypoint
    as expected.

        docker build -t test-image .
        docker run -it test-image --version
    """
    image_tag = "test-docker"
    cmd = [
        "python",
        "-c",
        'from toil_container import __version__; print(__version__)'
        ]
    build_docker_image(image_tag)

    container = Container().docker_call(
        image_tag,
        cmd=cmd,
        check_output=True,
        )

    assert __version__ in container.decode()


@pytest.mark.skipif(
    not utils.is_singularity_available(),
    reason="singularity is not available."
    )
def test_singularity_container():
    """
    Test the singularity image exists and its executable.

        singularity exec <test-image.simg> <command-parameters>
    """
    singularity_image = "docker://ubuntu"
    cmd = ["cat", "/etc/os-release"]

    # Create call
    output = Container().singularity_call(
        singularity_image,
        cmd=cmd,
        check_output=True
        )

    assert "VERSION" in output.decode()



# Toil Jobs and Options for testing
class ContainerizedCheckCallJob(ContainerCallJob):
    """
    Job created to test that check_call is used correctly by docker
    and singularity.
    """
    cmd = ["pwd"]
    cwd = None
    env = {}

    def run(self, jobStore):
        """Saves a Hello message in a file."""
        return self.check_call(self.cmd, cwd=self.cwd, env=self.env)


class ContainerizedCheckOutputJob(ContainerCallJob):
    """
    Job created to test that check_output is used correctly by docker
    and singularity.
    """
    cmd = ["pwd"]
    cwd = None
    env = {}

    def run(self, jobStore):
        """Saves a Hello message in a file."""
        return self.check_output(self.cmd, cwd=self.cwd, env=self.env)


def get_toil_test_parser():
    """Get test pipeline configuration using argparse."""
    # Add Toil options.
    parser = argparse.ArgumentParser()
    Job.Runner.addToilOptions(parser)

    # Parameters to run with docker or singularity
    settings = parser.add_argument_group("To run with docker or singularity:")

    settings.add_argument("--docker", default=False)
    settings.add_argument("--singularity", required=False)
    settings.add_argument("--shared-fs", required=False)

    return parser


def set_container_arguments(args, container_tool=None):
    """Add toil arguments necessary to run in containers."""
    shared_fs = os.environ["TEST_SHARED_FS"]

    if container_tool == "docker":
        image_tag = "test-toil"
        build_docker_image(image_tag)

        args += [
            "--docker", image_tag,
            "--shared-fs", shared_fs,
            ]

    elif container_tool == "singularity":
        singularity_image = "docker://ubuntu"

        args += [
            "--singularity", singularity_image,
            "--shared-fs", shared_fs,
            ]

    return args


def run_job_in_control_env(tmpdir, container_tool=None):
    """
    Run a Toil job in container with the option --singularity or --docker
    and --shared-fs SHARED-DIRECTORY to test the singularity wrapper
    is executing correctly the command inside the container.
    """
    # Create options for job
    workdir = join(str(tmpdir))
    jobstore = join(str(tmpdir), "jobstore")

    # Define arguments
    args = [jobstore, "--workDir", workdir]
    args = set_container_arguments(args, container_tool)
    parser = get_toil_test_parser()
    options = parser.parse_args(args)

    # Create jobs
    job_call = ContainerizedCheckCallJob(
        options=options,
        unitName="Check call pwd",
        )

    job_output = ContainerizedCheckOutputJob(
        options=options,
        unitName="Check output pwd",
        )

    # Make sure that cwd functionality in check_output works
    job_output.cwd = "/home"
    std_output = job_output.run(jobstore)
    assert "/home" in std_output

    # Make sure that cwd functionality in check_call works
    std_call = job_call.run(jobstore)
    assert 0 == std_call

    # Make sure workDir is used as the tmp directory inside the container
    # and that an ENV variable is passed to the container system call.
    message = "hello World"
    job_output.env = {"ISLAND": message}

    out_file = "bottle.txt"
    tmp_file_in_container = join(os.sep, "tmp", out_file)

    if container_tool == "docker":
        tmp_file_in_workdir = join(workdir, out_file)
    elif container_tool == "singularity":
        tmp_file_in_workdir = join(workdir, "tmp", out_file)
    else:
        tmp_file_in_workdir = join(workdir, out_file)
        tmp_file_in_container = tmp_file_in_workdir

    job_output.cmd = [
        "/bin/bash",
        "-c",
        "echo $ISLAND > {}".format(tmp_file_in_container)
        ]
    job_output.run(jobstore)

    with open(tmp_file_in_workdir) as f:
        assert message in f.read()


def run_parallel_jobs(tmpdir, container_tool=None):
    """
    Make sure parallel jobs work.
                    |
                parent_job
              /            \
    child_job_1             child_job_2
              \            /
                 tail_job
    """
    # Create options for job
    workdir = join(str(tmpdir))
    jobstore = join(str(tmpdir), "jobstore")

    args = [jobstore, "--workDir", workdir]
    args = set_container_arguments(args, container_tool)

    parser = get_toil_test_parser()
    options = parser.parse_args(args)

    # Create jobs
    parent_job = ContainerizedCheckOutputJob(
        options=options,
        unitName="Parent job",
        )
    child_job_1 = ContainerizedCheckOutputJob(
        options=options,
        unitName="Parallel Job 1",
        )
    child_job_2 = ContainerizedCheckOutputJob(
        options=options,
        unitName="Parallel Job 2",
        )
    tail_job = ContainerizedCheckOutputJob(
        options=options,
        unitName="Last Followon Job",
        )

    # Assign job commands
    out_file = "bottle.txt"
    tmp_file_in_container = join(os.sep, "tmp", out_file)

    if container_tool == "docker":
        tmp_file_in_workdir = join(workdir, out_file)
    elif container_tool == "singularity":
        tmp_file_in_workdir = join(workdir, "tmp", out_file)
    else:
        tmp_file_in_workdir = join(workdir, out_file)
        tmp_file_in_container = tmp_file_in_workdir

    base_cmd = ["/bin/bash", "-c"]

    parent_job.cmd = base_cmd + [
        "echo job1 >> {}".format(tmp_file_in_container)
        ]
    child_job_1.cmd = base_cmd + [
        "echo job2 >> {}".format(tmp_file_in_container)
        ]
    child_job_2.cmd = base_cmd + [
        "echo job3 >> {}".format(tmp_file_in_container)
        ]
    tail_job.cmd = base_cmd + [
        "echo job4 >> {}".format(tmp_file_in_container)
        ]

    # Create DAG
    parent_job.addChild(child_job_1)
    parent_job.addChild(child_job_2)
    parent_job.addFollowOn(tail_job)

    # Run jobs
    with Toil(options) as pipe:
        pipe.start(parent_job)

    # Test the output
    with open(tmp_file_in_workdir) as f:
        assert len(f.readlines()) == 4


def test_subprocess_toil_single_jobs(tmpdir):
    """Test to check subprocess calls work."""
    run_job_in_control_env(tmpdir)


@pytest.mark.skipif(
    not utils.is_docker_available(),
    reason="docker is not available."
    )
def test_docker_toil_single_jobs(tmpdir):
    """
    Test to check docker is setting correctly the /tmp dir,
    the working dir and the ENV variables inside the container.
    """
    run_job_in_control_env(tmpdir, container_tool="docker")


@pytest.mark.skipif(
    not utils.is_singularity_available(),
    reason="singularity is not available."
    )
def test_singularity_toil_single_jobs(tmpdir):
    """
    Test to check singularity is setting correctly the /tmp dir,
    the working dir and the ENV variables inside the container.
    """
    run_job_in_control_env(tmpdir, container_tool="singularity")


def test_subprocess_toil_parallel_jobs(tmpdir):
    """ Test to check parallel subprocess calls work."""
    run_parallel_jobs(tmpdir)


@pytest.mark.skipif(
    not utils.is_docker_available(),
    reason="docker is not available."
    )
def test_docker_toil_parallel_jobs(tmpdir):
    """ Test to check parallel docker containers run."""
    run_parallel_jobs(tmpdir, container_tool="docker")


@pytest.mark.skipif(
    not utils.is_singularity_available(),
    reason="singularity is not available."
    )
def test_singularity_toil_parallel_jobs(tmpdir):
    """ Test to check parallel singularity containers run."""
    run_parallel_jobs(tmpdir, container_tool="singularity")

