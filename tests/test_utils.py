"""toil_container version test."""

from toil import subprocess

from toil_container import utils


def test_which_util():
    """Test to check the which util is working."""
    std_out = subprocess.check_output(
        [utils.which("python"), "--version"], stderr=subprocess.STDOUT
    )
    assert "3.6" in std_out.decode()
