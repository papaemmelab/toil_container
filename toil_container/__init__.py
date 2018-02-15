"""toil_container module."""

from os.path import join
from os.path import abspath
from os.path import dirname

from toil_container.jobs import ContainerCallJob
from toil_container.parsers import (
    ContainerArgumentParser,
    ContainerShortArgumentParser,
    ToilShortArgumentParser
)

MODULE_ROOT = abspath(dirname(__file__))

with open(join(MODULE_ROOT, "VERSION"), "r") as f:
    VERSION = f.read().strip()

__version__ = VERSION
