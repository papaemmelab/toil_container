"""toil_container module."""

from toil_container.jobs import (
    ContainerCallJob
)

from toil_container.parsers import (
    ContainerArgumentParser,
    ContainerShortArgumentParser,
    ToilShortArgumentParser
)

with open("VERSION", "r") as f:
    VERSION = f.read().strip()

__version__ = VERSION
