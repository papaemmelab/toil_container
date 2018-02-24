"""toil_container jobs."""

from toil.job import Job

from toil_container import containers
from toil_container import exceptions
from toil_container.utils import subprocess


class ContainerJob(Job):

    """A job class with a `call` method for containerized system calls."""

    def __init__(self, options, *args, **kwargs):
        """
        Set toil's namespace `options` as an attribute.

        Use toil_container.

        Arguments:
            options (object): an `argparse.Namespace` object with toil options.
            args (list): positional arguments to be passed to `toil.job.Job`.
            kwargs (dict): key word arguments to be passed to `toil.job.Job`.
        """
        self.options = options
        super(ContainerJob, self).__init__(*args, **kwargs)

    def call(self, args, cwd=None, env=None, check_output=False):
        """
        Make a containerized call if images available, else use subprocess.

        Docker will be used if `self.options.docker` is set. Similarly,
        Singularity will be used if `self.options.singularity` is set.
        If neither case, `subprocess` will be used.

        If `self.options.workDir` is defined, this path will be used as the
        temporary directory within the containers.

        If `self.options.volumes` is available, these will be mounted
        inside the containers. `volumes` must be a list of tuples:

            [(<local_path>, <container_absolute_path>), ...]

        Arguments:
            args (list): list of command line arguments passed to the tool.
            cwd (str): current working directory.
            env (dict): environment variables to set inside container.
            check_output (bool): if true, returns stdout of system call.

        Returns:
            str: (check_output=True) stdout of the system call.
            int: (check_output=False) 0 if call succeed else raise error.

        Raises:
            toil_container.UsageError: if both `singularity` and
                `docker` are set in `self.options`. Or if invalid
                `volumes` are defined.

            toil_container.SystemCallError: if system call cannot be completed.
        """
        call_kwargs = dict(args=args, env=env, cwd=cwd)
        docker = getattr(self.options, "docker", None)
        singularity = getattr(self.options, "singularity", None)

        if singularity and docker:
            raise exceptions.UsageError(
                "Both docker and singularity can't be set "
                "at the same time."
                )

        if singularity or docker:
            call_kwargs["check_output"] = check_output

            if getattr(self.options, "workDir", None):
                call_kwargs["working_dir"] = self.options.workDir

            if getattr(self.options, "volumes", None):
                call_kwargs["volumes"] = self.options.volumes

            if singularity:
                call_kwargs["image"] = singularity
                call_function = containers.singularity_call
            else:
                call_kwargs["image"] = docker
                call_function = containers.docker_call

        elif check_output:
            call_function = subprocess.check_output

        else:
            call_function = subprocess.check_call

        errors = (
            exceptions.ContainerError,
            subprocess.CalledProcessError,
            OSError,
            )

        try:
            output = call_function(**call_kwargs)
        except errors as error:  # pylint: disable=catching-non-exception
            raise exceptions.SystemCallError(error)

        try:
            return output.decode()
        except AttributeError:
            return output
