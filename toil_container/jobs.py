"""toil_container jobs."""

import os
import sentry_sdk

from slugify import slugify
from toil import subprocess
from toil.batchSystems import registry
from toil.job import Job

from toil_container import containers, exceptions, utils

from . import lsf

# register the custom LSF Batch System
registry.addBatchSystemFactory("CustomLSF", lambda: lsf.CustomLSFBatchSystem)


class ContainerJob(Job):

    class Runner(Job.Runner):

        @staticmethod
        def startToil(job, options, tool_name, tool_release, use_sentry):
            """
            Wrap toil.Job.Runner.startToil with sentry.

            Arguments:
                job (obj): root job of the workflow.
                options (object): an `argparse.Namespace` object with toil options.
                tool_name (str): name of the tool.
                tool_release (str): version of the tool.
                use_sentry (bool): True if send error to sentry.
            
            Raises:
                Exception: any exceptions raised from Job.Runner.startToil.
            """
            try:
                Job.Runner.startToil(job, options)
            except Exception as error:
                if use_sentry:
                    utils.initialize_sentry(tool_name=tool_name, tool_release=tool_release)

                    with sentry_sdk.configure_scope() as scope:
                        scope.user = {'id': os.environ['USER']}

                    errors = utils.get_errors_from_toil_logs(options.writeLogs)

                    for error_message, traceback in errors.items():
                        print(f"sentry: report exception: {error_message}")
                        sentry_sdk.add_breadcrumb(message=traceback, level='error')
                        sentry_sdk.capture_message(error_message, level='error')

                raise error


    """A job class with a `call` method for containerized system calls."""

    def __init__(self, options, runtime=None, sentry=False, tool_name='', 
                tool_release='', *args, **kwargs):
        """
        Set toil's namespace `options` as an attribute.

        Note that `runtime (-W)` is custom LSF solutions that is ignored unless
        toil is run with `--batchSystem CustomLSF`. Please note that this hack
        encodes the requirements in the job's `unitName` resulting in longer
        log files names.

        Let us know if you need more custom parameters, e.g. `runtime_limit`,
        or if you know of a better solution (see: BD2KGenomics/toil#2065).

        Arguments:
            runtime (int): estimated run time for the job in minutes,
                ignored unless batchSystem is set to CustomLSF (-W).
            options (object): an `argparse.Namespace` object with toil options.
            args (list): positional arguments to be passed to `toil.job.Job`.
            kwargs (dict): key word arguments to be passed to `toil.job.Job`.
        """
        self.options = options
        self.sentry = sentry
        self.tool_name = tool_name
        self.tool_release = tool_release

        if not kwargs.get("displayName"):
            kwargs["displayName"] = self.__class__.__name__

        if getattr(options, "batchSystem", None) == "CustomLSF":
            data = {"runtime": runtime or os.getenv("TOIL_CONTAINER_RUNTIME")}
            kwargs["unitName"] = str(kwargs.get("unitName", "") or "")
            kwargs["unitName"] += lsf._encode_dict(data)

        super(ContainerJob, self).__init__(*args, **kwargs)

        # set jobName to displayName so that logs are named with displayName
        self.jobName = slugify(kwargs["displayName"], separator="_")

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
            toil_container.SystemCallError: if system call cannot be completed.
            toil_container.UsageError: if both `singularity` and `docker` are
                set in `self.options`. Or if invalid `volumes` are defined.
        """
        call_kwargs = dict(args=args, env=env, cwd=cwd)
        docker = getattr(self.options, "docker", None)
        singularity = getattr(self.options, "singularity", None)

        if singularity and docker:
            raise exceptions.UsageError("use docker or singularity, not both.")

        if singularity or docker:
            call_kwargs["check_output"] = check_output

            # used for testing only
            call_kwargs["remove_tmp_dir"] = getattr(self, "_rm_tmp_dir", True)

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
            call_function = utils.check_output

        else:
            call_function = utils.check_call

        errors = (exceptions.ContainerError, exceptions.SystemCallError, OSError)

        try:
            output = call_function(**call_kwargs)
        except errors as error:  # pylint: disable=catching-non-exception
            if self.sentry:
                utils.initialize_sentry(self.tool_name, self.tool_release)

                with sentry_sdk.configure_scope() as scope:
                    scope.user = {'id': os.environ['USER']} 
            
                sentry_sdk.capture_exception(error)
            raise exceptions.SystemCallError(error)

        try:
            return output.decode()
        except AttributeError:
            return output
