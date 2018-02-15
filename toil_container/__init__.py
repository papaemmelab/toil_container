"""toil_container module."""

from os.path import abspath
from os.path import dirname
from os.path import join

from toil_container.jobs import (
    ContainerCallJob
)

from toil_container.parsers import (
    ContainerArgumentParser,
    ContainerShortArgumentParser,
    ToilShortArgumentParser
)

# make sure we use absolute paths
ROOT = abspath(dirname(__file__))

with open(join(ROOT, "VERSION"), "r") as f:
    VERSION = f.read().strip()

__version__ = VERSION
