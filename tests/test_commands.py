"""=toil_container commands tests."""

from os.path import join

import pytest

from toil_container import commands


def test_toil_container(tmpdir):
    """Sample test for the main command."""
    #  Define arguments.
    message = "This is a test message for the Universe."
    outfile = join(str(tmpdir), "hello.txt")
    jobstore = join(str(tmpdir), "jobstore")
    total = 3
    args = [
        jobstore,
        "--message", message,
        "--outfile", outfile,
        "--total", str(total),
        ]

    # Get and validate options.
    parser = commands.get_parser()
    options = parser.parse_args(args)
    options = commands.process_parsed_options(options)

    # Call pipeline
    commands.run_toil(options)

    # Assert custom message is echoed in master log.
    with open(outfile) as f:
        assert len(f.read().split(message)) == total + 1


@pytest.fixture
def response():
    """
    Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    return 10


def test_fixture(response):
    """Sample test function with the pytest fixture as an argument."""
    assert response == 10
