"""toil_container parsers tests."""

import click
import pytest

from toil_container import exceptions
from toil_container import parsers

from .utils import Capturing
from .utils import SKIP_DOCKER
from .utils import SKIP_SINGULARITY
from .utils import DOCKER_IMAGE
from .utils import SINGULARITY_IMAGE


def check_help_toil(parser):
    with Capturing() as without_toil:
        try:
            parser.parse_args(["--help"])
        except SystemExit:
            pass

    with Capturing() as with_toil:
        try:
            parser.parse_args(["--help-toil"])
        except SystemExit:
            pass

    with_toil = "\n".join(with_toil)
    without_toil = "\n".join(without_toil)

    # by default toil options shouldn't be printed
    assert "toil core options" not in without_toil
    assert "TOIL OPTIONAL ARGS" in without_toil
    assert "toil arguments" in without_toil

    # check that toil options were added by default
    assert "toil core options" not in without_toil
    assert "toil core options" in with_toil


def test_help_toil():
    parser = parsers.ToilShortArgumentParser()
    check_help_toil(parser)


def test_parser_add_version():
    parser = parsers.ToilBaseArgumentParser(version="foo")
    assert "version" in parser.format_help()


def assert_container_parser_validates_image(image_flag, image, tmpdir):
    parser = parsers.ContainerArgumentParser()
    jobstore = tmpdir.join("jobstore").strpath

    # test parser has help-toil argument
    check_help_toil(parser)

    # by default container options should be added in both helps
    assert "container arguments" in parser.format_help()

    # can't pass docker and singularity at the same time
    args = [
        "--singularity-image", "foo",
        "--docker-image", "bar",
        tmpdir.join("jobstore").strpath,
        ]

    with pytest.raises(click.UsageError) as error:
        parser.parse_args(args)

    assert "You can't pass both" in str(error.value)

    # container_volumes only used for containers
    args = [
        "--container-volumes", "foo", "bar",
        tmpdir.join("jobstore").strpath,
        ]

    with pytest.raises(click.UsageError) as error:
        parser.parse_args(args)

    assert "--container-volumes should be used only " in str(error.value)

    # test valid image
    args = [image_flag, image, jobstore]
    assert parser.parse_args(args)

    # test invalid image
    with pytest.raises(exceptions.ValidationError):
        args = [image_flag, "florentino-ariza-img", jobstore]
        assert parser.parse_args(args)

    # test valid volumes
    args = [
        image_flag, image,
        "--container-volumes", tmpdir.mkdir("vol1").strpath, "/vol1",
        "--container-volumes", tmpdir.mkdir("vol2").strpath, "/vol2",
        "--workDir", tmpdir.mkdir("workDir").strpath,
        jobstore,
        ]

    assert parser.parse_args(args)

    # test invalid volumes, dst volume is not an absolute path
    args = [
        "--container-volumes", tmpdir.join("vol1").strpath, "vol1",
        image_flag, image,
        jobstore,
        ]

    with pytest.raises(exceptions.ValidationError):
        assert parser.parse_args(args)


@SKIP_DOCKER
def test_container_parser_validates_docker_image(tmpdir):
    assert_container_parser_validates_image(
        "--docker-image", DOCKER_IMAGE, tmpdir
        )


@SKIP_SINGULARITY
def test_container_parser_validates_singularity_image(tmpdir):
    assert_container_parser_validates_image(
        "--singularity-image", SINGULARITY_IMAGE, tmpdir
        )
