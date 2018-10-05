"""toil_container setup.py."""

from os.path import abspath
from os.path import dirname
from os.path import join
import json

from setuptools import find_packages
from setuptools import setup

# make sure we use absolute paths
ROOT = abspath(dirname(__file__))

# please put setup keywords in the setup.json to keep this file clean
with open(join(ROOT, "setup.json"), "r") as f:
    SETUP = json.load(f)

# see 4 > https://packaging.python.org/guides/single-sourcing-package-version/
with open(join(ROOT, "toil_container", "VERSION"), "r") as f:
    VERSION = f.read().strip()

setup(
    # single source package version
    version=VERSION,
    # in combination with recursive-includes in MANIFEST.in, non-python files
    # within the toil_container will be copied into the site-packages and
    # wheels installation directories
    include_package_data=True,
    # return a list all Python packages found within the ROOT directory
    packages=find_packages(),
    # pass parameters loaded from setup.json including author and version
    **SETUP
)
