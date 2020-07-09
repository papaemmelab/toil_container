"""Toil Container SLURM jobs tests."""

from . import utils


@utils.SKIP_SLURM
def test_custom_slurm_batch_system(tmpdir):
    utils.check_env_and_runtime(tmpdir, "CustomSlurm", "time=1")


@utils.SKIP_SLURM
def test_custom_slurm_resource_retry_runtime(tmpdir):
    utils.retry_runtime(tmpdir, "CustomSlurm")
