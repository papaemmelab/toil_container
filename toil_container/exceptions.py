"""toil_container specific exceptions."""


class ToilContainerException(Exception):

    """A base exception for toil_container."""


class DockerNotAvailableError(ToilContainerException):

    """A class to raise when docker is not available."""


class SingularityNotAvailableError(ToilContainerException):

    """A class to raise when singularity is not available."""
