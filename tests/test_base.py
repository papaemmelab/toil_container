import os

from toil import subprocess

from toil_container import base


def test_with_retries(tmpdir):
    test_path = tmpdir.join("test")

    def _test():
        if not os.path.isfile(test_path.strpath):
            test_path.write("hello")
            subprocess.check_call(["rm", "/"])
        return

    base.with_retries(_test)


def test_encode_decode_resources():
    expected = {"runtime": 1}
    e_string = base._encode_dict(expected)
    obtained = base._decode_dict(e_string)
    assert base._encode_dict({}) == ""
    assert base._decode_dict("") == {}
    assert expected == obtained
