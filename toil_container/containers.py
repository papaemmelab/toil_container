"""
Library to manage docker and singularity calls through the containers tools.

Docker uses a API for python, while singularity API doesn't support python2.

Based on the docker implementation of:
https://github.com/BD2KGenomics/toil/blob/master/src/toil/lib/docker.py

Based on the singularity implementation of:
https://github.com/vgteam/toil--bindg/blob/master/src/toil_vg/singularity.py

Docker images can be run by prefacing the input image with docker://
In this case, Singularity will download, convert, and cache the image on the
fly. This cache can be set with SINGULARITY_CACHEDIR, and defaults to the
user's home directory. This cache can be a major bottleneck when repeatedly
more different images than it can hold (not very many). So for this type of
usage pattern (concurrent or short consecutive calls to different images),
it is best to run Singularity images natively.
"""

import logging
import uuid
import subprocess

from docker.errors import ContainerError
from docker.errors import ImageNotFound
import docker

from toil_container import utils

_LOGGER = logging.getLogger(__name__)


class Container(object):

    """Class to manage docker and singularity calls."""

    def __init__(self):
        """Assign attributes unique to each container."""
        if utils.is_docker_available():
            self.docker_client = docker.from_env()
            self.container_name = ""

    def docker_call(
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
            image (str): name of the singularity image.
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
            CalledProcessorError: if the container invocation returns a
            non-zero exit code.
        """
        utils.is_docker_available(raise_error=True)

        if not self.container_name:
            self.container_name = self._get_container_name(image)

        docker_parameters = {}
        docker_parameters["command"] = cmd
        docker_parameters["detach"] = check_output
        docker_parameters["entrypoint"] = ""
        docker_parameters["environment"] = env or {}
        docker_parameters["name"] = self.container_name
        docker_parameters["volumes"] = {}

        # Set parameters for managing directories if options are defined
        if shared_fs:
            docker_parameters["volumes"][shared_fs] = {
                "bind": shared_fs,
                "mode": "rw"
                }

        if working_dir:
            docker_parameters["volumes"][working_dir] = {
                "bind": "/tmp",
                "mode": "rw"
                }

        if cwd:
            docker_parameters["working_dir"] = cwd

        exceptions = (
            ContainerError,
            ImageNotFound,
            subprocess.CalledProcessError
            )

        try:
            container = self.docker_client.containers.run(
                image,
                **docker_parameters
                )

            # If detached wait to get the system exit to get logs before remove.
            if check_output:
                container.wait()
                output = container.logs()
            else:
                output = 0
            self._prune_docker_container(self.container_name)

            return output

        except exceptions as stderr:
            self._prune_docker_container(self.container_name)
            raise subprocess.CalledProcessError(0, cmd=cmd, output=stderr)

    @staticmethod
    def singularity_call(
            image,
            cmd=None,
            cwd=None,
            env=None,
            check_output=None,
            working_dir=None,
            shared_fs=None):
        """
        Execute parameters in a singularity container via subprocess.

        The resulting command is in the format:

            singularity -q exec
                <list-of-singularity-params>
                <singularity-image>
                <list-of-cmd-params-executed-inside-container>

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
            CalledProcessorError: if the container invocation returns a
            non-zero exit code.
        """
        singularity_command = utils.is_singularity_available(
            raise_error=True,
            path=True
            )
        singularity_parameters = []

        # Set parameters for managing directories if options are defined
        if shared_fs:
            singularity_parameters += [
                "--bind", "{fs}:{fs}".format(fs=shared_fs)
                ]
        if working_dir:
            singularity_parameters += [
                "--contain",
                "--workdir", working_dir
                ]
        if cwd:
            singularity_parameters += ["--pwd", cwd]

        # Setup the outgoing subprocess call for singularity
        command = [singularity_command, "-q", "exec"]
        command += singularity_parameters or []
        command += [image]
        command += cmd or []

        subprocess_kwargs = {}

        # Singularity inherits the subprocess environment
        subprocess_kwargs["env"] = env

        if check_output:
            call_method = subprocess.check_output
        else:
            call_method = subprocess.check_call

        _LOGGER.info("Calling singularity with %s", repr(command))
        out = call_method(command, **subprocess_kwargs)
        return out

    @staticmethod
    def _get_container_name(image):
        """
        Create a unique name for the container.

        Arguments:
            image (str): name of the image used to run the container.

        Returns:
            str: a unique string of image name plus a unique random identifier.
        """
        return image.replace(":latest", "") + "-" + str(uuid.uuid4())

    def _prune_docker_container(self, container_name):
        """
        Remove running container.

        Arguments:
            container_name (str): name of unique container that is running.
        """
        if not container_name:
            container_name = self.container_name
        container = self.docker_client.containers.get(container_name)
        container.stop()
        container.remove()
