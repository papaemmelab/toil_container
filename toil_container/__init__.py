"""toil_container module."""

from os.path import abspath
from os.path import dirname
from os.path import join

from toil_container.containers import docker_call, singularity_call

from toil_container.jobs import ContainerJob

from toil_container.parsers import ContainerArgumentParser, ToilShortArgumentParser

from toil_container.exceptions import (
    ContainerError,
    DockerNotAvailableError,
    SingularityNotAvailableError,
    ToilContainerException,
    ToolNotAvailableError,
    UsageError,
)

# make sure we use absolute paths
ROOT = abspath(dirname(__file__))

with open(join(ROOT, "VERSION"), "r", encoding="utf8") as f:
    VERSION = f.read().strip()

__version__ = VERSION
