"""toil_container specific exceptions."""


class ToilContainerException(Exception):

    """A base exception for toil_container."""


class UsageError(ToilContainerException):

    """A class to raise when improper usage."""


class ContainerError(ToilContainerException):

    """A class to raise when a container call fails."""


class SystemCallError(ToilContainerException):

    """A class to raise when a system call cannot be completed."""


class ValidationError(ToilContainerException):

    """A class to raise for validation errors."""


class ToolNotAvailableError(ToilContainerException):

    """A base exception to raise when tools are not available."""


class DockerNotAvailableError(ToolNotAvailableError):

    """A class to raise when docker is not available."""


class SingularityNotAvailableError(ToolNotAvailableError):

    """A class to raise when singularity is not available."""
