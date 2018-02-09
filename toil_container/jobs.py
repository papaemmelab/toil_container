"""toil_container jobs."""

import subprocess

from toil.job import Job

from toil_container.containers import Container


class BaseJob(Job):

    """Job base class used to share variables and methods across steps."""

    def __init__(self, options=None, lsf_tags=None, unitName="", **kwargs):
        """
        Use this base class to share variables across pipelines steps.

        Arguments:
            unitName (str): string that will be used as the lsf jobname.
            options (object): an argparse name space object.
            lsf_tags (list): a list of custom supported tags by leukgen
                see this file /ifs/work/leukgen/opt/toil_lsf/python2/lsf.py.
            kwargs (dict): key word arguments to be passed to toil.job.Job.
        """
        # If unitName is not passed, we set the class name as the default.
        if unitName == "":
            unitName = self.__class__.__name__

        # This is a custom solution for LSF options in MSKCC.
        if getattr(options, "batchSystem", None) == "LSF":
            unitName = "" if unitName is None else str(unitName)
            unitName += "".join("<LSF_%s>" % i for i in lsf_tags or [])

        # make options an attribute.
        self.options = options

        # example of a shared variable.
        self.shared_variable = "Hello World"

        super(BaseJob, self).__init__(unitName=unitName, **kwargs)

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


class HelloWorld(BaseJob):

    def run(self, fileStore):
        """Say hello to the world."""
        with open(self.options.outfile, "w") as outfile:
            outfile.write(self.shared_variable)


class HelloWorldMessage(BaseJob):

    def __init__(self, message, *args, **kwargs):
        """Load message variable as attribute."""
        self.message = message
        super(HelloWorldMessage, self).__init__(*args, **kwargs)

    def run(self, fileStore):
        """Send message to the world."""
        with open(self.options.outfile, "w") as outfile:
            outfile.write(self.options.message)

        # Log message to master.
        fileStore.logToMaster(self.message)
