"""toil_container containers tests."""

from os.path import join
from os.path import abspath
from os.path import dirname
import os
import argparse

import docker
import pytest

from toil_container import __version__
from toil_container import utils
from toil_container.containers import docker_call
from toil_container.containers import singularity_call

from .utils import Capturing


SKIP_DOCKER = pytest.mark.skipif(
    not utils.is_docker_available(),
    reason="docker is not available."
    )

SKIP_SINGULARITY = pytest.mark.skipif(
    not utils.is_singularity_available(),
    reason="singularity is not available."
    )

IMAGE = "docker://ubuntu"


def assert_call_function(call_function, tmpdir):
    # test check_output False
    with Capturing() as output:
        exit_status = call_function(IMAGE, cmd=["ls", "/"])

    assert exit_status == 0
    assert "bin" in " ".join(output)  # check stdout and stderr are printed

    # test check_output True
    assert "bin" in call_function(IMAGE, cmd=["ls", "/"], check_output=True)

    # test toil_container.ContainerError is raised with bad command
    with pytest.raises() as error:
        call_function(IMAGE, cmd=["rm", "/bin"])

    assert "raised during the container call" in error.value

    # test cwd, env, shared_fs and working_dir options
    script_name, output_name = "env.sh", "result.txt"
    env_key, env_value = "FOO", "BAR"
    shared_fs = tmpdir.join("shared_fs")
    working_dir = tmpdir.join("working_dir")
    env_sh = shared_fs.join(script_name)
    env_sh.write("echo ${0} > tmp/{1}".format(env_key, output_name))
    cwd = "/SHARED_FS"

    assert "BAR" in call_function(
        IMAGE,
        cmd=["bash", script_name],
        env={env_key: env_value},
        cwd=cwd,
        shared_fs=(shared_fs, cwd),
        working_dir=working_dir,
        )

    if os.path.isdir(working_dir.join("tmp").strpath):
        output_path = working_dir.join("tmp").join(output_name)
    else:
        output_path = working_dir.join(output_name)

    assert env_value in output_path.read()


@SKIP_DOCKER
def test_docker_call_check_call(tmpdir):
    assert_call_function(docker_call, tmpdir)


@SKIP_SINGULARITY
def test_singularity_call_check_call(tmpdir):
    assert_call_function(singularity_call, tmpdir)


# ROOT = abspath(join(dirname(__file__), ".."))

# def build_docker_image(image_tag):
#     """Build image from Dockerfile if not created yet."""
#     try:
#         client = docker.from_env()
#         client.images.get(image_tag)
#     except docker.errors.ImageNotFound:
#         client.images.build(path=ROOT, rm=True, tag=image_tag)

# def set_container_arguments(args, container_tool=None):
#     """Add toil arguments necessary to run in containers."""
#     shared_fs = os.environ["TEST_SHARED_FS"]

#     if container_tool == "docker":
#         image_tag = "test-toil"
#         build_docker_image(image_tag)

#         args += [
#             "--docker", image_tag,
#             "--shared-fs", shared_fs,
#             ]

#     elif container_tool == "singularity":
#         singularity_image = "docker://ubuntu"

#         args += [
#             "--singularity", singularity_image,
#             "--shared-fs", shared_fs,
#             ]

#     return args


# def run_job_in_control_env(tmpdir, container_tool=None):
#     """
#     Run a Toil job in container with the option --singularity or --docker
#     and --shared-fs SHARED-DIRECTORY to test the singularity wrapper
#     is executing correctly the command inside the container.
#     """
#     # Create options for job
#     workdir = join(str(tmpdir))
#     jobstore = join(str(tmpdir), "jobstore")

#     # Define arguments
#     args = [jobstore, "--workDir", workdir]
#     args = set_container_arguments(args, container_tool)
#     parser = get_toil_test_parser()
#     options = parser.parse_args(args)

#     # Create jobs
#     job_call = ContainerizedCheckCallJob(
#         options=options,
#         unitName="Check call pwd",
#         )

#     job_output = ContainerizedCheckOutputJob(
#         options=options,
#         unitName="Check output pwd",
#         )

#     # Make sure that cwd functionality in check_output works
#     job_output.cwd = "/home"
#     std_output = job_output.run(jobstore)
#     assert "/home" in std_output

#     # Make sure that cwd functionality in check_call works
#     std_call = job_call.run(jobstore)
#     assert 0 == std_call

#     # Make sure workDir is used as the tmp directory inside the container
#     # and that an ENV variable is passed to the container system call.
#     message = "hello World"
#     job_output.env = {"ISLAND": message}

#     out_file = "bottle.txt"
#     tmp_file_in_container = join(os.sep, "tmp", out_file)

#     if container_tool == "docker":
#         tmp_file_in_workdir = join(workdir, out_file)
#     elif container_tool == "singularity":
#         tmp_file_in_workdir = join(workdir, "tmp", out_file)
#     else:
#         tmp_file_in_workdir = join(workdir, out_file)
#         tmp_file_in_container = tmp_file_in_workdir

#     job_output.cmd = [
#         "/bin/bash",
#         "-c",
#         "echo $ISLAND > {}".format(tmp_file_in_container)
#         ]
#     job_output.run(jobstore)

#     with open(tmp_file_in_workdir) as f:
#         assert message in f.read()


# def run_parallel_jobs(tmpdir, container_tool=None):
#     """
#     Make sure parallel jobs work.
#                     |
#                 parent_job
#               /            \
#     child_job_1             child_job_2
#               \            /
#                  tail_job
#     """
#     # Create options for job
#     workdir = join(str(tmpdir))
#     jobstore = join(str(tmpdir), "jobstore")

#     args = [jobstore, "--workDir", workdir]
#     args = set_container_arguments(args, container_tool)

#     parser = get_toil_test_parser()
#     options = parser.parse_args(args)

#     # Create jobs
#     parent_job = ContainerizedCheckOutputJob(
#         options=options,
#         unitName="Parent job",
#         )
#     child_job_1 = ContainerizedCheckOutputJob(
#         options=options,
#         unitName="Parallel Job 1",
#         )
#     child_job_2 = ContainerizedCheckOutputJob(
#         options=options,
#         unitName="Parallel Job 2",
#         )
#     tail_job = ContainerizedCheckOutputJob(
#         options=options,
#         unitName="Last Followon Job",
#         )

#     # Assign job commands
#     out_file = "bottle.txt"
#     tmp_file_in_container = join(os.sep, "tmp", out_file)

#     if container_tool == "docker":
#         tmp_file_in_workdir = join(workdir, out_file)
#     elif container_tool == "singularity":
#         tmp_file_in_workdir = join(workdir, "tmp", out_file)
#     else:
#         tmp_file_in_workdir = join(workdir, out_file)
#         tmp_file_in_container = tmp_file_in_workdir

#     base_cmd = ["/bin/bash", "-c"]

#     parent_job.cmd = base_cmd + [
#         "echo job1 >> {}".format(tmp_file_in_container)
#         ]
#     child_job_1.cmd = base_cmd + [
#         "echo job2 >> {}".format(tmp_file_in_container)
#         ]
#     child_job_2.cmd = base_cmd + [
#         "echo job3 >> {}".format(tmp_file_in_container)
#         ]
#     tail_job.cmd = base_cmd + [
#         "echo job4 >> {}".format(tmp_file_in_container)
#         ]

#     # Create DAG
#     parent_job.addChild(child_job_1)
#     parent_job.addChild(child_job_2)
#     parent_job.addFollowOn(tail_job)

#     # Run jobs
#     with Toil(options) as pipe:
#         pipe.start(parent_job)

#     # Test the output
#     with open(tmp_file_in_workdir) as f:
#         assert len(f.readlines()) == 4


# def test_subprocess_toil_single_jobs(tmpdir):
#     """Test to check subprocess calls work."""
#     run_job_in_control_env(tmpdir)


# @pytest.mark.skipif(
#     not utils.is_docker_available(),
#     reason="docker is not available."
#     )
# def test_docker_toil_single_jobs(tmpdir):
#     """
#     Test to check docker is setting correctly the /tmp dir,
#     the working dir and the ENV variables inside the container.
#     """
#     run_job_in_control_env(tmpdir, container_tool="docker")


# @pytest.mark.skipif(
#     not utils.is_singularity_available(),
#     reason="singularity is not available."
#     )
# def test_singularity_toil_single_jobs(tmpdir):
#     """
#     Test to check singularity is setting correctly the /tmp dir,
#     the working dir and the ENV variables inside the container.
#     """
#     run_job_in_control_env(tmpdir, container_tool="singularity")


# def test_subprocess_toil_parallel_jobs(tmpdir):
#     """ Test to check parallel subprocess calls work."""
#     run_parallel_jobs(tmpdir)


# @pytest.mark.skipif(
#     not utils.is_docker_available(),
#     reason="docker is not available."
#     )
# def test_docker_toil_parallel_jobs(tmpdir):
#     """ Test to check parallel docker containers run."""
#     run_parallel_jobs(tmpdir, container_tool="docker")


# @pytest.mark.skipif(
#     not utils.is_singularity_available(),
#     reason="singularity is not available."
#     )
# def test_singularity_toil_parallel_jobs(tmpdir):
#     """ Test to check parallel singularity containers run."""
#     run_parallel_jobs(tmpdir, container_tool="singularity")

