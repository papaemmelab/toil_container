"""toil_container validators tests."""

from os.path import join
import pytest

from toil_container import exceptions
from toil_container import validators


def test_validate_patterns_are_files(tmpdir):
    """Create multiple files and test test_validate_patterns_are_files."""
    tmpdir_path = str(tmpdir)

    for i in range(5):
        with open(join(tmpdir_path, "empty" + str(i)), "w") as _:
            pass

    for i in range(11, 15):
        with open(join(tmpdir_path, "not_empty" + str(i)), "w") as f:
            f.write("I'm not empty.")

    empty = [join(tmpdir_path, "empty*")]
    not_empty = [join(tmpdir_path, "not_empty*")]
    none_existing = ["florentino", "ariza*"]
    none_file = [tmpdir_path]

    # Check empty files exist.
    assert validators.validate_patterns_are_files(empty, check_size=False)

    # Check files exist amd are not empty.
    assert validators.validate_patterns_are_files(not_empty, check_size=True)

    # Check that empty files raise error with default setting.
    with pytest.raises(exceptions.ValidationError) as _:
        validators.validate_patterns_are_files(empty)

    # Check that empty files raise error with flag.
    with pytest.raises(exceptions.ValidationError) as _:
        validators.validate_patterns_are_files(empty, check_size=True)

    # Check that pattern is not file.
    with pytest.raises(exceptions.ValidationError) as _:
        validators.validate_patterns_are_files(none_file, check_size=True)

    # Check that empty files raise error with flag.
    with pytest.raises(exceptions.ValidationError) as _:
        validators.validate_patterns_are_files(empty, check_size=True)

    # Check that invalid patterns raise ValidationError error.
    with pytest.raises(exceptions.ValidationError) as _:
        validators.validate_patterns_are_files(none_existing, check_size=True)


def test_validate_patterns_are_dirs(tmpdir):
    """test_validate_patterns_are_dirs."""
    tmpdir_path = str(tmpdir)
    file_patterns = [join(tmpdir_path, "a_file")]
    existing_patterns = [tmpdir_path]
    none_existing_patterns = ["florentino", "ariza*"]

    # Touch the file.
    with open(file_patterns[0], "w") as _:
        pass

    # Check empty files exist.
    assert validators.validate_patterns_are_dirs(existing_patterns)

    # Check that empty files raise error with default setting.
    with pytest.raises(exceptions.ValidationError) as _:
        validators.validate_patterns_are_dirs(none_existing_patterns)

    # Check that empty files raise error with flag.
    with pytest.raises(exceptions.ValidationError) as _:
        validators.validate_patterns_are_dirs(file_patterns)
