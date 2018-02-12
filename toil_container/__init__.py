"""toil_container module."""

from os.path import join
from os.path import abspath
from os.path import dirname
import json

from toil_container.jobs import ContainerCallJob
from toil_container.parsers import (
    ToilContainerArgumentParser,
    ToilContainerShortArgumentParser,
    ToilShortArgumentParser
)

with open(join("setup.json"), "r") as f:
    SETUP = json.load(f)

__version__ = SETUP.get("version")

__author__ = SETUP.get("author")
