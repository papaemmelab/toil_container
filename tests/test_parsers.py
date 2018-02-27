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


def assert_parser_volumes(image_flag, image, tmpdir):
    # test valid volumes
    args = [
        image_flag, image,
        "--volumes", tmpdir.mkdir("vol1").strpath, "/vol1",
        "--volumes", tmpdir.mkdir("vol2").strpath, "/vol2",
        "--workDir", tmpdir.mkdir("workDir").strpath,
        "jobstore",
        ]

    assert parsers.ContainerArgumentParser().parse_args(args)

    # test invalid volumes, dst volume is not an absolute path
    args = [
        "--volumes", tmpdir.join("vol1").strpath, "vol1",
        image_flag, image,
        "jobstore",
        ]

    with pytest.raises(exceptions.ValidationError):
        parsers.ContainerArgumentParser().parse_args(args)


def test_help_toil():
    check_help_toil(parsers.ToilShortArgumentParser())


def test_help_toil_container_parser():
    parser = parsers.ContainerArgumentParser()
    check_help_toil(parser)
    assert "container arguments" in parser.format_help()


def test_parser_add_version():
    parser = parsers.ToilBaseArgumentParser(version="foo")
    assert "version" in parser.format_help()


def test_container_parser_cant_use_docker_and_singularity_together():
    with pytest.raises(click.UsageError) as error:
        args = ["--singularity", "i", "--docker", "j", "jobstore"]
        parsers.ContainerArgumentParser().parse_args(args)

    assert "You can't pass both" in str(error.value)


def test_volumes_only_used_with_containers():
    with pytest.raises(click.UsageError) as error:
        args = ["--volumes", "foo", "bar", "jobstore"]
        parsers.ContainerArgumentParser().parse_args(args)

    assert "--volumes should be used only " in str(error.value)


@SKIP_DOCKER
def test_container_parser_docker_valid_image():
    args = ["--docker", DOCKER_IMAGE, "jobstore"]
    assert parsers.ContainerArgumentParser().parse_args(args)


@SKIP_DOCKER
def test_container_parser_docker_invalid_image():
    with pytest.raises(exceptions.ValidationError):
        args = ["--docker", "florentino-ariza-img", "jobstore"]
        assert parsers.ContainerArgumentParser().parse_args(args)


@SKIP_DOCKER
def test_container_parser_docker_volumes(tmpdir):
    assert_parser_volumes("--docker", DOCKER_IMAGE, tmpdir)


@SKIP_SINGULARITY
def test_container_parser_singularity_valid_image():
    args = ["--singularity", SINGULARITY_IMAGE, "jobstore"]
    assert parsers.ContainerArgumentParser().parse_args(args)


@SKIP_SINGULARITY
def test_container_parser_singularity_invalid_image():
    with pytest.raises(exceptions.ValidationError):
        args = ["--singularity", "florentino-ariza-img", "jobstore"]
        assert parsers.ContainerArgumentParser().parse_args(args)


@SKIP_SINGULARITY
def test_container_parser_singularity_volumes(tmpdir):
    assert_parser_volumes("--singularity", SINGULARITY_IMAGE, tmpdir)
