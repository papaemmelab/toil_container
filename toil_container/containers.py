"""
Module to manage docker and singularity calls through the containers tools.

Docker uses a API for python, while singularity API doesn't support python2.

Based on the docker implementation of:
https://github.com/BD2KGenomics/toil/blob/master/src/toil/lib/docker.py

Based on the singularity implementation of:
https://github.com/vgteam/toil-vg/blob/master/src/toil_vg/singularity.py
"""

from __future__ import print_function

from tempfile import mkdtemp
import os
import shutil
import sys
import uuid

import docker

from toil_container.utils import get_container_error
from toil_container.utils import is_docker_available
from toil_container.utils import is_singularity_available
from toil_container.utils import subprocess

_TMP_PREFIX = "toil_container_tmp_"


def singularity_call(
        image,
        args=None,
        cwd=None,
        env=None,
        check_output=None,
        working_dir=None,
        volumes=None,
        remove_tmp_dir=True):
    """
    Execute parameters in a singularity container via subprocess.

    Singularity will be called with the following command:

        singularity -q exec
            --bind <shared_fs>:<shared_fs>     # if shared_fs is provided
            --contain --workdir <working_dir>  # if working_dir is provided
            --pwd {cwd}                        # if cwd is provided
            <image> <args>

    Docker images can be run by prefacing the input image with 'docker://'.
    In this case, Singularity will download, convert, and cache the image
    on the fly. This cache can be set with SINGULARITY_CACHEDIR, and
    defaults to the user's home directory. This cache can be a major
    bottleneck when repeatedly more different images than it can hold
    (not very many). So for this type of usage pattern (concurrent or short
    consecutive calls to different images), it is best to run Singularity
    images natively.

    Arguments:
        image (str): name/path of the image.
        args (list): list of command line arguments passed to the tool.
        cwd (str): current working directory.
        env (dict): environment variables to set inside container.
        check_output (bool): check_output or check_call behavior.
        working_dir (str): path to a working directory. If passed, a tmpdir
            will be created inside and will be mounted to /tmp.
        volumes (list): list of tuples (src-path, dst-path) to be mounted,
            dst-path must be absolute path.
        remove_tmp_dir (bool): remove tmpdir created inside `working_dir`.

    Returns:
        str: (check_output=True) stdout of the system call.
        int: (check_output=False) 0 if call succeed else non-0.

    Raises:
        toil_container.ContainerError: if the container invocation fails.
        toil_container.SingularityNotAvailableError: singularity not installed.
    """
    singularity_path = is_singularity_available(raise_error=True, path=True)

    # ensure singularity doesn't overwrite $HOME by pointing to dummy dir
    # /tmp will be mapped to work_dir/scratch/tmp and removed after the call
    home_dir = ".unused_home"
    work_dir = mkdtemp(prefix=_TMP_PREFIX, dir=working_dir)
    os.makedirs(os.path.join(work_dir, "scratch", "tmp", home_dir))
    singularity_args = [
        "--scratch", "/tmp",
        "--home", "{}:/tmp/{}".format(os.getcwd(), home_dir),
        "--workdir", work_dir,
        ]

    # set parameters for managing directories if options are defined
    if volumes:
        for src, dst in volumes:
            singularity_args += ["--bind", "{}:{}".format(src, dst)]

    if cwd:
        singularity_args += ["--pwd", cwd]

    # setup the outgoing subprocess call for singularity
    command = [singularity_path, "-q", "exec"] + singularity_args
    command += [image] + (args or [])

    if check_output:
        call = subprocess.check_output
    else:
        call = subprocess.check_call

    try:
        output = call(command, env=env)
        error = False
    except (subprocess.CalledProcessError, OSError) as error:
        pass

    if remove_tmp_dir:
        try:
            shutil.rmtree(work_dir)
        except:  # pylint: disable=W0702
            pass

    if error:
        raise get_container_error(error)

    try:
        return output.decode()
    except AttributeError:
        return output


def docker_call(
        image,
        args=None,
        cwd=None,
        env=None,
        check_output=None,
        working_dir=None,
        volumes=None,
        remove_tmp_dir=True):
    """
    Execute parameters in a docker container via docker-python API.

    See: https://docker-py.readthedocs.io/en/stable/

    Arguments:
        image (str): name/path of the image.
        args (list): list of command line arguments passed to the tool.
        cwd (str): current working directory.
        env (dict): environment variables to set inside container.
        check_output (bool): check_output or check_call behavior.
        working_dir (str): path to a working directory. If passed, a tmpdir
            will be created inside and will be mounted to the container /tmp.
        volumes (list): list of tuples (src-path, dst-path) to be mounted,
            dst-path must be absolute path.
        remove_tmp_dir (bool): remove tmpdir created inside `working_dir`.

    Returns:
        str: (check_output=True) stdout of the system call.
        int: (check_output=False) 0 if call succeed else raise error.

    Raises:
        toil_container.ContainerError: if the container invocation fails.
        toil_container.DockerNotAvailableError: when docker not available.
    """
    is_docker_available(raise_error=True)
    container_name = "container-" + str(uuid.uuid4())
    work_dir = None
    kwargs = {}
    kwargs["command"] = args
    kwargs["entrypoint"] = ""
    kwargs["environment"] = env or {}
    kwargs["name"] = container_name
    kwargs["volumes"] = {}

    # Set parameters for managing directories if options are defined
    if volumes:
        for src, dst in volumes:
            kwargs["volumes"][src] = {"bind": dst, "mode": "rw"}

    if working_dir:
        # if working_dir is passed, we need to make sure it will be unique
        work_dir = mkdtemp(prefix=_TMP_PREFIX, dir=working_dir)
        kwargs["volumes"][work_dir] = {"bind": "/tmp", "mode": "rw"}

    if cwd:
        kwargs["working_dir"] = cwd

    client = docker.from_env(version="auto")
    expected_errors = (
        docker.errors.ImageNotFound,
        docker.errors.APIError,
        )

    try:
        container = client.containers.run(image, detach=True, **kwargs)
        exit_status = container.wait()
        error = False
    except expected_errors as error:
        pass

    if remove_tmp_dir:
        try:
            shutil.rmtree(work_dir)
        except:  # pylint: disable=W0702
            pass

    if error:
        _remove_docker_container(container_name)
        raise get_container_error(error)

    if check_output:
        output = container.logs(stdout=True, stderr=False)
        stderr = container.logs(stdout=True, stderr=True)

    else:  # print logs to stdout and stderr as subprocess.check_call
        output = exit_status
        stderr = container.logs(stdout=False, stderr=True)
        stdout = container.logs(stdout=True, stderr=False)
        print(stderr, file=sys.stderr)
        print(stdout, file=sys.stdout)

    container.stop()
    container.remove()

    if exit_status != 0:
        error = docker.errors.ContainerError(
            container=container,
            exit_status=exit_status,
            command=args,
            image=image,
            stderr=stderr,
            )

        raise get_container_error(error)

    try:
        return output.decode()
    except AttributeError:
        return output


def _remove_docker_container(container_name):
    try:
        client = docker.from_env(version="auto")
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
    except docker.errors.APIError:
        pass
