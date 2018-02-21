"""toil_container jobs."""

import subprocess

# from toil.batchSystems import registry
from toil.job import Job

from toil_container.containers import docker_call
from toil_container.containers import singularity_call


class ContainerJob(Job):

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

    def __init__(self, options, *args, **kwargs):
        """
        Set `options` namespace as an attribute.

        Arguments:
            options (object): an `argparse.Namespace` object.
            args (list): positional arguments to be passed to `toil.job.Job`.
            kwargs (dict): key word arguments to be passed to `toil.job.Job`.
        """
        self.options = options
        super(ContainerJob, self).__init__(*args, **kwargs)

    # def call(
    #         self,
    #         cmd,
    #         cwd=None,
    #         env=None,
    #         check_output=False,
    #         singularity_image=None,
    #         docker_image=None,
    #         ):
    #     """"""
    #     call_kwargs = {}

    #     if singularity_image and docker_image:
    #         raise error

    #     if singularity_image is None:
    #         singularity_image = getattr(
    #             self.options, "singularity_image", None
    #             ):

    #     if self.options.singularity:
    #         return Container().singularity_call(
    #             self.options.singularity,
    #             cmd=cmd,
    #             cwd=cwd,
    #             env=env,
    #             check_output=True,
    #             working_dir=self.options.workDir,
    #             shared_fs=self.options.shared_fs,
    #         )


# from toil_container.lsf import CustomLSFBatchSystem
# registry.addBatchSystemFactory("CustomLSF", _CustomLSFBatchSystemFactory)
