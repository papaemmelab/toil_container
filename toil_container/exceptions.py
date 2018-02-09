"""toil_container specific exceptions."""


class PackageBaseException(Exception):

    """A base exception for toil_container."""


class ValidationError(PackageBaseException):

    """A class to raise when a validation error occurs."""


class MissingRequirementError(PackageBaseException):

    """A class to raise when a requirement is missing."""


class MissingOutputError(PackageBaseException):

    """A class to raise when a file that should exist is missing."""


class ConfigurationError(PackageBaseException):

    """A class to raise when is not properly configured."""


class ImplementationError(PackageBaseException):

    """A class to raise when is not properly implemented."""


class CantBeRunError(PackageBaseException):

    """A class to raise when a pipeline just cannot be run."""


class MissingDataError(PackageBaseException):

    """A class to raise when data is missing."""
