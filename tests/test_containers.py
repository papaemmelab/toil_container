"""toil_container containers tests."""

from multiprocessing import Process
from os.path import join
import getpass
import os

import docker
import pytest

from toil_container import __version__
from toil_container import exceptions
from toil_container.containers import _TMP_PREFIX
from toil_container.containers import _remove_docker_container
from toil_container.containers import docker_call
from toil_container.containers import singularity_call

from .utils import DOCKER_IMAGE
from .utils import ROOT
from .utils import SINGULARITY_IMAGE
from .utils import SKIP_DOCKER
from .utils import SKIP_SINGULARITY
from .utils import Capturing


def assert_option_check_output(call, img):
    # test check_output True
    assert "bin" in call(img, args=["ls", "/"], check_output=True)

    # test toil_container.ContainerError is raised with bad command
    with pytest.raises(exceptions.ContainerError) as error:
        call(img, args=["rm", "/florentino-ariza-volume"])

    assert "raised during the container system call" in str(error.value)


def assert_option_cwd(call, img):
    assert "bin" in call(img, ["ls", ".."], cwd="/bin", check_output=True)


def assert_option_env(call, img):
    args = ["bash", "-c", "echo $FOO"]
    assert "BAR" in call(img, args, env={"FOO": "BAR"}, check_output=True)

    # check container doesn't inherit environment
    os.environ["FOO"] = "BAR"
    args = ["bash", "-c", "echo $FOO"]
    assert "BAR" not in call(img, args, check_output=True)


def assert_parallel_call(call, img):
    p1 = Process(target=lambda: call(img, ["sleep", "1"]))
    p2 = Process(target=lambda: call(img, ["sleep", "1"]))
    p1.start()
    p2.start()
    p1.join()
    p2.join()


def assert_option_volumes(call, img, tmpdir):
    vsrc = tmpdir.strpath
    fsrc = tmpdir.join("foo")
    vdst = join(os.sep, "SHARED")
    fdst = join(vdst, "foo")
    call(img, ["bash", "-c", "echo bar > " + fdst], volumes=[(vsrc, vdst)])
    assert "bar" in fsrc.read()


def assert_option_working_dir(call, img, tmpdir):
    args = ["bash", "-c", "echo bar > /tmp/foo"]
    dont_remove = tmpdir.mkdir("dont")
    call(img, args, working_dir=dont_remove.strpath, remove_tmp_dir=False)
    tmpfile = next(dont_remove.visit(_TMP_PREFIX + "*/foo"))
    assert "bar" in tmpfile.read()

    remove = tmpdir.mkdir("remove")
    call(img, args, working_dir=remove.strpath, remove_tmp_dir=True)
    assert not list(remove.visit(_TMP_PREFIX + "*"))


@SKIP_DOCKER
def test_docker_check_output_false_prints_to_stdout_and_stderr():
    with Capturing() as output:
        exit_status = docker_call(DOCKER_IMAGE, args=["ls", "/"])

    assert exit_status == 0
    assert "bin" in " ".join(output)  # check stdout and stderr are printed


@SKIP_DOCKER
def test_docker_check_output():
    assert_option_check_output(docker_call, DOCKER_IMAGE)


@SKIP_DOCKER
def test_docker_cwd():
    assert_option_cwd(docker_call, DOCKER_IMAGE)


@SKIP_DOCKER
def test_docker_env():
    assert_option_env(docker_call, DOCKER_IMAGE)


@SKIP_DOCKER
def test_docker_parallel():
    assert_parallel_call(docker_call, DOCKER_IMAGE)


@SKIP_DOCKER
def test_docker_volumes(tmpdir):
    assert_option_volumes(docker_call, DOCKER_IMAGE, tmpdir)


@SKIP_DOCKER
def test_docker_working_dir(tmpdir):
    assert_option_working_dir(docker_call, DOCKER_IMAGE, tmpdir)


@SKIP_SINGULARITY
def test_singularity_check_output():
    assert_option_check_output(singularity_call, SINGULARITY_IMAGE)


@SKIP_SINGULARITY
def test_singularity_cwd():
    assert_option_cwd(singularity_call, SINGULARITY_IMAGE)


@SKIP_SINGULARITY
def test_singularity_env():
    assert_option_env(singularity_call, SINGULARITY_IMAGE)


@SKIP_SINGULARITY
def test_singularity_parallel():
    assert_parallel_call(singularity_call, SINGULARITY_IMAGE)


@SKIP_SINGULARITY
def test_singularity_volumes(tmpdir):
    assert_option_volumes(singularity_call, SINGULARITY_IMAGE, tmpdir)


@SKIP_SINGULARITY
def test_singularity_working_dir(tmpdir):
    assert_option_working_dir(singularity_call, SINGULARITY_IMAGE, tmpdir)


@SKIP_SINGULARITY
def test_singularity_doesnt_overwrite_home():
    args = ["bash", "-c", "ls /home"]
    skip = ".singularity/docker"
    output = singularity_call(SINGULARITY_IMAGE, args, check_output=True)
    output = "".join(i for i in output.split() if skip not in i)
    assert getpass.getuser() not in output


@SKIP_DOCKER
def test_remove_docker_container():
    name = "florentino-ariza"
    client = docker.from_env(version="auto")
    container = client.containers.create(DOCKER_IMAGE, ["ls"], name=name)
    container.start()
    _remove_docker_container(name)

    with pytest.raises(docker.errors.NotFound) as error:
        client.containers.get(name)

    assert name in str(error.value)


@SKIP_DOCKER
def test_docker_container():
    python_args = "from toil_container import __version__; print(__version__)"
    args = ["python", "-c", python_args]
    image_tag = "test-toil-container-image"
    client = docker.from_env(version="auto")
    client.images.build(path=ROOT, rm=True, tag=image_tag)
    assert __version__ in docker_call(image_tag, args, check_output=True)
