"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?
You might be tempted to import things from __main__ later, but that will
cause problems, the code will get executed twice:

    - When you run `python -m toil_container` python will execute
      `__main__.py` as a script. That means there won't be any
      `toil_container.__main__` in `sys.modules`.

    - When you import __main__ it will get executed again (as a module) because
      there's no `toil_container.__main__` in `sys.modules`.

Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

from toil_container import commands


def main():
    """toil_container main command."""
    commands.main()

if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
