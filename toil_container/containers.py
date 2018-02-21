"""
Module to manage docker and singularity calls through the containers tools.

Docker uses a API for python, while singularity API doesn't support python2.

Based on the docker implementation of:
https://github.com/BD2KGenomics/toil/blob/master/src/toil/lib/docker.py

Based on the singularity implementation of:
https://github.com/vgteam/toil-vg/blob/master/src/toil_vg/singularity.py
"""

import uuid
import subprocess

import docker

from toil_container import utils


class SingularityContainer():

    """Class to manage singularity calls."""

    def __init__(self):
        """Assign attributes unique to each container."""
        self.singularity_path = utils.is_singularity_available(
            raise_error=True,
            path=True
            )

    def call(
            self,
            image,
            cmd=None,
            cwd=None,
            env=None,
            check_output=None,
            working_dir=None,
            shared_fs=None):
        """
        Execute parameters in a singularity container via subprocess.

        Singularity will be called with the following command:

            singularity -q exec
                --bind <shared_fs>:<shared_fs>     # if shared_fs is provided
                --contain --workdir <working_dir>  # if working_dir is provided
                --pwd {cwd}                        # if cwd is provided
                <image> <cmd>

        Docker images can be run by prefacing the input image with 'docker://'.
        In this case, Singularity will download, convert, and cache the image
        on the fly. This cache can be set with SINGULARITY_CACHEDIR, and
        defaults to the user's home directory. This cache can be a major
        bottleneck when repeatedly more different images than it can hold
        (not very many). So for this type of usage pattern (concurrent or short
        consecutive calls to different images), it is best to run Singularity
        images natively.

        Arguments:
            image (str): name of the singularity image.
            cmd (list): list of command line arguments passed to the tool.
            cwd (str): current working directory.
            env (dict): environment variables to set inside container.
            check_output (bool): check_output or check_call behavior.
            working_dir (dict): directory where commands will be run.
            shared_fs (str): file shared dir to bind volumens inside container.

        Returns:
            str: (check_output=True) stdout of the system call.
            int: (check_output=False) 0 if call succeed else non-0.

        Raises:
            toil_container.exceptions.ContainerCallError: if the container
                invocation returns a non-zero exit code.
        """
        singularity_args = []

        # set parameters for managing directories if options are defined
        if shared_fs:
            singularity_args += ["--bind", "{0}:{0}".format(shared_fs)]

        if working_dir:
            singularity_args += ["--contain", "--workdir", working_dir]

        if cwd:
            singularity_args += ["--pwd", cwd]

        # setup the outgoing subprocess call for singularity
        command = [self.singularity_path, "-q", "exec"] + singularity_args
        command += [image] + (cmd or [])

        if check_output:
            call = subprocess.check_output
        else:
            call = subprocess.check_call

        try:
            output = call(command, env=env)
        except subprocess.CalledProcessError as error:
            utils.raise_container_error(error)

        return output


class DockerContainer():

    """Class to manage docker calls."""

    def __init__(self):
        """Assign attributes unique to each container."""
        utils.is_docker_available(raise_error=True)
        self.client = docker.from_env(version="auto")
        self.name = "container-" + str(uuid.uuid4())

    def call(
            self,
            image,
            cmd=None,
            cwd=None,
            env=None,
            check_output=None,
            working_dir=None,
            shared_fs=None):
        """
        Execute parameters in a docker container via docker-python API.

        See: https://docker-py.readthedocs.io/en/stable/

        Arguments:
            image (str): name of the docker image.
            cmd (list): list of command line arguments passed to the tool.
            cwd (str): current working directory.
            env (dict): environment variables to set inside container.
            check_output (bool): check_output or check_call behavior.
            working_dir (dict): directory where commands will be run.
            shared_fs (str): file shared dir to bind volumens inside container.

        Returns:
            str: (check_output=True) stdout of the system call.
            int: (check_output=False) 0 if call succeed else raise error.

        Raises:
            toil_container.exceptions.ContainerCallError: if the container
                invocation returns a non-zero exit code.
        """
        run_kwargs = {}
        run_kwargs["command"] = cmd
        run_kwargs["detach"] = check_output
        run_kwargs["entrypoint"] = ""
        run_kwargs["environment"] = env or {}
        run_kwargs["name"] = self.name
        run_kwargs["volumes"] = {}

        # Set parameters for managing directories if options are defined
        if shared_fs:
            run_kwargs["volumes"][shared_fs] = {
                "bind": shared_fs,
                "mode": "rw"
                }

        if working_dir:
            run_kwargs["volumes"][working_dir] = {
                "bind": "/tmp",
                "mode": "rw"
                }

        if cwd:
            run_kwargs["working_dir"] = cwd

        try:
            output = 0
            container = self.client.containers.run(image, **run_kwargs)

            # if detached wait to get the system exit to get logs
            if check_output:
                container.wait()
                output = container.logs()

            self._prune_container()
            return output

        except docker.errors.DockerException as error:
            self._prune_container()
            utils.raise_container_error(error)

    def _prune_container(self):
        """Remove running Docker container."""
        container = self.client.containers.get(self.name)
        container.stop()
        container.remove()
