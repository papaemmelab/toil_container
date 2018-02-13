"""toil_container utils."""

import os
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


def which(program):
    """
    Python implementation to mimic the behavior of the UNIX 'which' command,
    to locate a program file in the user's path.

    https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python

    Arguments:
        program (str): command to be tested. Can be relative or absolute path.

    Return:
        str: program file in the user's path.
    """
    fpath, _ = os.path.split(program)
    if fpath:
        if _is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if _is_exe(exe_file):
                return exe_file
    return None


def _is_exe(fpath):
    """
    Check if fpath is executable.

    Arguments:
        fpath (str): path to check if it's executable.

    Return:
        bool: True if executable, else False.
    """
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
