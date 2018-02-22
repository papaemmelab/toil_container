"""toil_container validators."""

from toil_container import exceptions
from toil_container.containers import docker_call
from toil_container.containers import singularity_call


def validate_docker_image(image, volumes=None, working_dir=None):
    """Validate a docker image."""
    _validate_image(docker_call, image, volumes, working_dir)
    return image


def validate_singularity_image(image, volumes=None, working_dir=None):
    """Validate a singularity image."""
    _validate_image(singularity_call, image, volumes, working_dir)
    return image


def _validate_image(call, image, volumes, working_dir):
    """Call will fail if invalid image, volumes or working_dir are passed."""
    try:
        call(image, ["ls"], volumes=volumes, working_dir=working_dir)
    except exceptions.ContainerError as error:
        raise exceptions.ValidationError(
            "Invalid container configuration: "
            "{}: {}".format(type(error), str(error))
            )
