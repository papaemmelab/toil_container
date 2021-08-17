"""toil_container tests utils."""

from io import StringIO
from os.path import abspath
from os.path import dirname
from os.path import join
import os
import sys

import pytest

from toil_container import utils

ROOT = abspath(join(dirname(__file__), ".."))
DOCKER_IMAGE = "ubuntu:latest"
SKIP_LSF = pytest.mark.skipif(not utils.which("bsub"), reason="bsub is not available.")
SKIP_DOCKER = pytest.mark.skipif(
    not utils.is_docker_available(), reason="docker is not available."
)

SKIP_SINGULARITY = pytest.mark.skipif(
    not utils.is_singularity_available(), reason="singularity is not available."
)

if os.path.isfile(os.getenv("CACHED_SINGULARITY_IMAGE", "/")):
    SINGULARITY_IMAGE = os.getenv("CACHED_SINGULARITY_IMAGE")
else:
    SINGULARITY_IMAGE = "docker://" + DOCKER_IMAGE


class Capturing(list):

    """
    Capture stdout and stderr of a function call.

    See: https://stackoverflow.com/questions/16571150

    Example:

        with Capturing() as output:
            do_something(my_object)
    """

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout
