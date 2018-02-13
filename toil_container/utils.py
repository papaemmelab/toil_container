"""toil_container utils."""

import os
import subprocess

from docker.errors import APIError
import docker
import requests

from toil_container import exceptions


def is_docker_available(raise_error=False, path=False):
    """
    Check if docker is available to run in the current environment.

    Arguments:
        raise_error (bool): flag to raise error when command is unavailable.
        path (bool): flag to return location of the command in the user's path.

    Returns:
        bool: True if docker is available.

    Raises:
        OSError: if the raise_error flag was passed as an argument and the
        command is not available to execute.
    """
    try:
        # Test docker is running
        client = docker.from_env()
        is_available = client.ping()

        if path:
            return which("docker")
        return is_available

    except (requests.exceptions.ConnectionError, APIError):
        if raise_error:
            raise exceptions.DockerNotAvailableError()
        return False


def is_singularity_available(raise_error=False, path=False):
    """
    Check if singularity is available to run in the current environment.

    Arguments:
        raise_error (bool): flag to raise error when command is unavailable.
        path (bool): flag to return location of the command in the user's path.

    Returns:
        bool: True if singularity is available.
        str: absolute location of the file in the user's path.

    Raises:
        OSError: if the raise_error flag was passed as an argument and the
        command is not available to execute.
    """
    try:
        # Test it's available. Similar to `singularity --version &> /dev/null`
        file_null = open(os.devnull, 'w')
        subprocess.check_call(["singularity", "--version"], stdout=file_null)

        if path:
            return which('singularity')
        return True

    except OSError:
        if raise_error:
            raise exceptions.SingularityNotAvailableError()
        return False


def which(program):
    """
    Locate a program file in the user's path.

    Python implementation to mimic the behavior of the UNIX 'which' command
    And shutil.which() is not supported in python 2.x.

    See: https://stackoverflow.com/questions/377017

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
    Check if fpath is executable for the current user.

    Arguments:
        fpath (str): relative or absolute path.

    Return:
        bool: True if execution is granted, else False.
    """
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
