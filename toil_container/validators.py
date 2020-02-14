"""toil_container validators."""

from toil_container import exceptions
from toil_container.containers import docker_call
from toil_container.containers import singularity_call


def validate_docker(image, volumes=None, working_dir=None, env=None):
    """Validate a docker image."""
    _validate_image(docker_call, image, volumes, working_dir, env)
    return image


def validate_singularity(image, volumes=None, working_dir=None, env=None):
    """Validate a singularity image."""
    _validate_image(singularity_call, image, volumes, working_dir, env)
    return image


def _validate_image(call, image, volumes, working_dir, env):
    """Call will fail if invalid image, volumes or working_dir are passed."""
    cmd = ["bash", "-c"]

    if volumes:
        cmd += [" && ".join(["ls " + i[1] for i in volumes])]
    elif env:
        cmd += ["echo " + "${}".format(list(env)[0])]
    else:
        cmd += ["echo"]

    try:
        kwargs = dict(volumes=volumes, working_dir=working_dir, env=env)
        return call(image, cmd, check_output=True, **kwargs)
    except exceptions.ContainerError as error:
        raise exceptions.ValidationError(
            "Invalid container configuration: " "{}: {}".format(type(error), str(error))
        )
