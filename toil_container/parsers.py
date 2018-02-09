"""toil_container pasers."""

import argparse

from toil.job import Job
import click

from toil_container import __version__
from toil_container import utils


CUSTOM_TOIL_ACTIONS = [
    argparse.Action(
        ["TOIL EXTRA ARGS"],
        dest="",
        default=argparse.SUPPRESS,
        help="see --help-toil for a full list of toil parameters",
    ),
    argparse.Action(
        [],
        dest="jobStore",
        help="the location of the job store for the workflow. "
        "See --help-toil for more information [REQUIRED]"
    )
    ]


class _ToilHelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        """Print parser help and exist whilst adding a flag to the parser."""
        parser.show_toil_groups = True
        parser.print_help()
        parser.exit()


class ToilArgumentParser(argparse.ArgumentParser):

    """
    A Argument parser for toil pipelines.

    Toil options are automatically added, but hidden by default in the
    help print. However, the custom `--help-toil` option will include
    toil arguments sections in the help print.

    Additionally, a container section is included (this can be turned off).
    """

    def __init__(self, *args, **kwargs):
        """
        Add Toil options, `--help-toil` and container section to parser.

        Include the following keywords in kwargs to switch of the version
        and container groups:

            add_container_group (bool): add section for container runs.
            add_version (bool): add version option using `__version__`.
        """
        add_container_group = kwargs.pop("add_container_group", True)
        add_version = kwargs.pop("add_version", True)

        # Set ArgumentDefaultsHelpFormatter as the default formatter.
        kwargs["formatter_class"] = kwargs.get(
            "formatter_class", argparse.ArgumentDefaultsHelpFormatter
        )

        super(ToilArgumentParser, self).__init__(*args, **kwargs)

        # Add package version.
        if add_version:
            self.add_argument(
                "-v", "--version",
                action="version",
                version="%(prog)s " + __version__
            )

        self.add_argument(
            "--help-toil",
            action=_ToilHelpAction, default=argparse.SUPPRESS,
            help="print help with full list of Toil arguments and exit"
        )

        # Add toil options.
        Job.Runner.addToilOptions(self)

        # Parameters to run with docker or singularity.
        self.add_container_group = add_container_group
        if add_container_group:
            settings = self.add_argument_group("container arguments")

            settings.add_argument(
                "--docker",
                help="name of the docker image, available in daemon",
                default=None,
                metavar="DOCKER-IMAGE-NAME",
                required=False,
            )

            settings.add_argument(
                "--singularity",
                help=(
                    "path of the singularity image (.simg) to jobs be run "
                    "inside singularity containers"
                ),
                required=False,
                metavar="SINGULARITY-IMAGE-PATH",
                type=click.Path(
                    file_okay=True,
                    readable=True,
                    resolve_path=True,
                    exists=True,
                )
            )

            settings.add_argument(
                "--shared-fs",
                help="shared file system path to be mounted in containers",
                required=False,
                type=click.Path(
                    file_okay=True,
                    readable=True,
                    resolve_path=True,
                    exists=True,
                )
            )

    def get_help_groups(self, show_toil_groups):
        """Decide whether to show toil options or not."""
        action_groups = []
        actions = []

        for action_group in self._action_groups:
            is_toil_group = action_group.title.startswith("toil")
            is_toil_group |= "Logging Options" in action_group.title

            if not is_toil_group or (is_toil_group and show_toil_groups):
                action_groups.append(action_group)
                actions += action_group._group_actions

        return actions, action_groups

    def format_help(self):
        """Include toil options if `self.show_toil_groups` is True."""
        formatter = self._get_formatter()

        # decide whether to show toil options or not
        show_toil_groups = getattr(self, "show_toil_groups", False)
        actions, action_groups = self.get_help_groups(show_toil_groups)

        # usage, the CUSTOM_TOIL_ACTIONS are just for display
        formatter.add_usage(
            self.usage,
            actions + ([] if show_toil_groups else CUSTOM_TOIL_ACTIONS),
            self._mutually_exclusive_groups
        )

        # description
        formatter.add_text(self.description)

        # positionals, optionals and user-defined groups
        for action_group in action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # add custom toil section
        if not show_toil_groups:
            formatter.start_section("toil arguments")
            formatter.add_arguments(CUSTOM_TOIL_ACTIONS)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()

    def parse_args(self, args=None, namespace=None):
        """Validate parsed options."""
        args = super(ToilArgumentParser, self).parse_args(
            args=args, namespace=namespace,
            )

        # Check container options are ok.
        if self.add_container_group:
            if args.singularity and args.docker:
                raise click.UsageError(
                    "You can't pass both --singularity and --docker."
                )

            if args.shared_fs and not any([args.docker, args.singularity]):
                raise click.UsageError(
                    "--shared-fs should be used only with "
                    "--singularity or --docker."
                )

            if args.shared_fs and args.workDir:
                if args.shared_fs not in args.workDir:
                    raise click.UsageError(
                        "The --workDir must be available in the "
                        "--shared-fs directory."
                    )

            if args.docker and not utils.is_docker_available():
                raise click.UsageError(
                    "Docker is not currently available in your environment."
                )

            if args.singularity and not utils.is_singularity_available():
                raise click.UsageError(
                    "Singularity is not currently available in "
                    "your environment."
                )

        return args
