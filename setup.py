#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""toil_container setup.py."""

from os.path import join
from os.path import abspath
from os.path import dirname
import io
import json

from setuptools import find_packages
from setuptools import setup

ROOT = abspath(dirname(__file__))
CONF = join(ROOT, "toil_container", "data", "setup.json")


def read(path, **kwargs):
    """Return content of a file."""
    return io.open(path, encoding=kwargs.get("encoding", "utf8")).read()


# Please put setup keywords in the setup.json to keep this file clean.
with open(CONF, "r") as f:
    SETUP = json.load(f)

setup(
    # Load description from README.
    long_description=read(join(ROOT, "README.md")),

    # In combination with MANIFEST.in, package non-python files included
    # inside the toil_container will be copied to the
    # site-packages installation directory.
    include_package_data=True,

    # Return a list all Python packages found within the ROOT directory.
    packages=find_packages(),

    # Pass parameters loaded from setup.json including author and version.
    **SETUP
)
