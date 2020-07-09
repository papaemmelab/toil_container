"""Toil Container SGE jobs tests."""

from . import utils


@utils.SKIP_SGE
def test_custom_sge_batch_system(tmpdir):
    utils.check_env_and_runtime(tmpdir, "CustomSGE", "h_rt=00:1:00")


@utils.SKIP_SGE
def test_custom_sge_resource_retry_runtime(tmpdir):
    utils.retry_runtime(tmpdir, "CustomSGE")
