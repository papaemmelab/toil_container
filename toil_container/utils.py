"""toil_container utils."""

import subprocess

from docker.errors import APIError
import docker
import requests

from toil_container import exceptions


def is_docker_available(raise_error=False):
    """
    Check if docker is available to run in the current environment.

    Returns:
        bool: True if docker is available.
    """
    client = docker.from_env()
    try:
        return client.ping()
    except (requests.exceptions.ConnectionError, APIError):
        if raise_error:
            raise exceptions.DockerNotAvailableError()
        return False


def is_singularity_available(raise_error=False):
    """
    Check if singularity is available to run in the current environment.

    Returns:
        bool: True if singularity is available.
    """
    try:
        subprocess.check_call(["singularity", "--version"])
        return True
    except OSError:
        if raise_error:
            raise exceptions.SingularityNotAvailableError()
        return False
