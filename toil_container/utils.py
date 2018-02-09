"""toil_container utils."""

import os
import tarfile
import subprocess

from docker.errors import APIError
import docker
import requests


def force_link(src, dst):
    """Force a link between src and dst."""
    try:
        os.unlink(dst)
        os.link(src, dst)
    except OSError:
        os.link(src, dst)


def force_symlink(src, dst):
    """Force a symlink between src and dst."""
    try:
        os.unlink(dst)
        os.symlink(src, dst)
    except OSError:
        os.symlink(src, dst)


def tar_dir(output_path, source_dir):
    """
    Compress a directory in

    Arguments:
        output_path (str): path to output file.
        source_dir (str): path to directory to be compressed.
    """
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def is_docker_available():
    """
    Check if docker is available to run in the current environment.

        Returns:
            bool: True if docker is available.
    """
    client = docker.from_env()
    try:
        return client.ping()
    except (requests.exceptions.ConnectionError, APIError):
        return False


def is_singularity_available():
    """
    Check if singularity is available to run in the current environment.

        Returns:
            bool: True if singularity is available.
    """
    try:
        subprocess.check_call(["singularity", "--version"])
        return True
    except OSError:
        return False
