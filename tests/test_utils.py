"""toil_container version test."""
import subprocess

from toil_container import utils


def test_which_util():
    """Test to check the which util is working."""
    std_out = subprocess.check_output(
        [utils.which("python"), "--version"], stderr=subprocess.STDOUT
    )
    assert std_out.decode().startswith("Python 3")
