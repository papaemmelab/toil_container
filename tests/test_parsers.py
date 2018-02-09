"""toil_container parsers tests."""

import argparse

import click
import pytest

from toil_container import parsers

from .utils import Capturing


def test_help_toil():
    parser = parsers.ToilArgumentParser()
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

    # By default container options should be added in both helps.
    assert "container arguments" in without_toil
    assert "container arguments" in with_toil

    # By default toil options shouldn't be printed.
    assert "toil core options" not in without_toil
    assert "toil arguments" in without_toil
    assert "TOIL EXTRA ARGS" in without_toil

    # Check that toil options were added by default.
    assert "toil core options" not in without_toil


def test_parse_args(tmpdir):
    shared_fs = tmpdir.mkdir("shared_fs")
    work_dir = tmpdir.mkdir("workdir")
    image = tmpdir.join("test.img")
    jobstore = tmpdir.join("jobstore")
    image.write("not empty")
    parser = parsers.ToilArgumentParser()

    # Can't pass docker and singularity at the same time.
    args = [
        "--singularity", image.strpath,
        "--docker", image.strpath,
        jobstore.strpath,
    ]

    with pytest.raises(click.UsageError) as error:
        parser.parse_args(args)

    assert "You can't pass both" in str(error.value)

    # shared-fs only used for containers.
    args = [
        "--shared-fs", shared_fs.strpath,
        "--workDir", work_dir.strpath,
        jobstore.strpath,
    ]

    with pytest.raises(click.UsageError) as error:
        parser.parse_args(args)

    assert "--shared-fs should be used only " in str(error.value)

    # workDir must be inside shared-fs.
    args = [
        "--singularity", image.strpath,
        "--shared-fs", shared_fs.strpath,
        "--workDir", work_dir.strpath,
        jobstore.strpath,
    ]

    with pytest.raises(click.UsageError) as error:
        parser.parse_args(args)

    assert "The --workDir must be available " in str(error.value)
