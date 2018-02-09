"""toil_container module."""

from os.path import join
from os.path import abspath
from os.path import dirname
import json

from .jobs import (
    ContainerCallJob,
)

from .parsers import (
    ToilContainerHelpParser,
    ToilShortHelpParser,
)

ROOT = abspath(dirname(__file__))

with open(join("setup.json"), "r") as f:
    SETUP = json.load(f)

__version__ = SETUP.get("version")

__author__ = SETUP.get("author")
