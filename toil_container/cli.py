# -*- coding: utf-8 -*-

"""Console script for toil_container."""

import click


@click.command()
def main(args=None):
    """Console script for toil_container."""
    click.echo("Replace this message by putting your code into "
               "toil_container.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
