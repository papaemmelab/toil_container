"""toil_container jobs."""

import subprocess

from toil.job import Job

from toil_container.containers import Container


class ContainerCallJob(Job):

    """
    A job class with abstract methods for system calls.

    This class includes abstract methods `check_call` and `check_output` which
    will use `toil` or `singularity` containers to execute system calls.

    In order to do this, the `options` namespace must have the properties
    `docker_image_path` or `singularity_image_path`, else python's `subprocess`
    will be used for system calls.

    Use `toil_container.ContainerOptionsParser` to include `--docker` and
    `--singularity` in the options namespace!
    """

    def __init__(self, options, unitName="", **kwargs):
        """
        Set `options` namespace as an attribute.

        Arguments:
            options (object): an argparse name space object.
            unitName (str): string to refer to the job.
            kwargs (dict): key word arguments to be passed to `toil.job.Job`.
        """
        # If unitName is not passed, we set the class name as the default.
        if unitName == "":
            unitName = self.__class__.__name__

        # This is a custom solution for LSF options in MSKCC.
        if getattr(options, "batchSystem", None) == "LSF":
            unitName = self._set_msk_lsf_tags(unitName, kwargs)

        # make options an attribute.
        self.options = options

        super(ContainerCallJob, self).__init__(unitName=unitName, **kwargs)

    def check_call(self, cmd, cwd=None, env=None):
        """
        Wrap the subprocess.check_call, if any container tool was chosen.

        Arguments:
            cmd (list): list of command line arguments passed to the tool.
            cwd (str): current working directory.
            env (dict): environment variables to set inside container.

        Returns:
            int: 0 if call succeed else raise error.
        """
        if getattr(self.options, "singularity", None):
            return Container().singularity_call(
                self.options.singularity,
                cmd=cmd,
                cwd=cwd,
                env=env,
                check_output=False,
                working_dir=self.options.workDir,
                shared_fs=self.options.shared_fs,
                )
        elif getattr(self.options, "docker", None):
            return Container().docker_call(
                self.options.docker,
                cmd=cmd,
                cwd=cwd,
                env=env,
                check_output=False,
                working_dir=self.options.workDir,
                shared_fs=self.options.shared_fs,
                )
        return subprocess.check_call(
            cmd,
            cwd=cwd,
            env=env
            )

    def check_output(self, cmd, cwd=None, env=None):
        """
        Wrap the subprocess.check_output, if any container tool was chosen.

        Arguments:
            cmd (list): list of command line arguments passed to the tool.
            cwd (str): current working directory.
            env (dict): environment variables to set inside container.

        Returns:
            str: stdout of the system call.
        """
        if self.options.singularity:
            return Container().singularity_call(
                self.options.singularity,
                cmd=cmd,
                cwd=cwd,
                env=env,
                check_output=True,
                working_dir=self.options.workDir,
                shared_fs=self.options.shared_fs,
                )
        elif self.options.docker:
            return Container().docker_call(
                self.options.docker,
                cmd=cmd,
                cwd=cwd,
                env=env,
                check_output=True,
                working_dir=self.options.workDir,
                shared_fs=self.options.shared_fs,
                )
        return subprocess.check_output(
            cmd,
            cwd=cwd,
            env=env
            )

    @ staticmethod
    def _set_msk_lsf_tags(unitName, kwargs):
        """
        [MSK ONLY] Use unitName to pass perjob LSF configuration to lsf.py.

        see this file /ifs/work/leukgen/opt/toil_lsf/python2/lsf.py.
        """
        lsf_tags = kwargs.get("lsf_tags", [])
        unitName = "" if unitName is None else str(unitName)
        return "".join("<LSF_%s>" % i for i in lsf_tags)
