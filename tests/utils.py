"""toil_container tests utils."""

from cStringIO import StringIO
import sys


class Capturing(list):

    """
    Capture stdout of a function call.

    See: https://stackoverflow.com/questions/16571150

    Example:

        with Capturing() as output:
            do_something(my_object)
    """

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout
