"""toil_container tests utils."""

from io import BytesIO
from os.path import abspath
from os.path import dirname
from os.path import join
import os
import sys
import requests
from datetime import datetime
import time

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
        sys.stdout = self._stringio = BytesIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout

def assert_sentry(error_time, expected_title):
    token = '2f257d64885f40da918f8be21e04bbbfe6b1d8c34cad45748631cd315aa70f3b'
    url = 'https://sentry.io/api/0/projects/papaemmelab/toil_strelka/issues/'
    r = requests.get(url=url, headers={'Authorization': 'Bearer {}'.format(token)})
    r = r.json()
    success = False
    for error in r:
        try:
            title = error['metadata']['value']
        except KeyError:
            title = error['metadata']['title']
        lastSeen = datetime.strptime(error['lastSeen'], '%Y-%m-%dT%H:%M:%S.%fZ')
        delta_time = (error_time - lastSeen).total_seconds()
        if (expected_title in title) & (delta_time<1):
            print('success')
            issue_id = error['id']
            url = 'https://sentry.io/api/0/issues/{}/'.format(issue_id)
            # requests.delete(url, headers={'Authorization': 'Bearer {}'.format(token)})
            success =  True

    return success