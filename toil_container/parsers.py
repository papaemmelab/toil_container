"""toil_container pasers."""

import argparse

from toil.job import Job
import click

from toil_container import validators

SHOW_TOILGROUPS_PROPERTY = "_show_toil_groups"
SHOW_CONTGROUPS_PROPERTY = "_show_container_groups"
CUSTOM_TOIL_ACTIONS = [
    argparse.Action(
        [],
        dest="jobStore",
        help="the location of the job store for the workflow. "
        "See --help-toil for more toil options and information [REQUIRED]",
    )
]


class _ToilHelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        """Print parser help and exist whilst adding a flag to the parser."""
        setattr(parser, SHOW_TOILGROUPS_PROPERTY, True)
        parser.print_help()
        parser.exit()


class _ContainerHelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        """Print parser help and exist whilst adding a flag to the parser."""
        setattr(parser, SHOW_CONTGROUPS_PROPERTY, True)
        parser.print_help()
        parser.exit()


class ToilBaseArgumentParser(argparse.ArgumentParser):

    """Add toil options to argument parser."""

    def __init__(self, version=None, **kwargs):
        """
        Add Toil options to parser.

        Arguments:
            version (str): optionally add a version argument.
            kwargs (dict): argparse.ArgumentParser key word arguments.
        """
        if not kwargs.get("formatter_class"):
            kwargs["formatter_class"] = argparse.ArgumentDefaultsHelpFormatter

        super().__init__(**kwargs)

        if version:
            self.add_argument(
                "-v", "--version", action="version", version="%(prog)s " + str(version)
            )

        Job.Runner.addToilOptions(self)


class ToilShortArgumentParser(ToilBaseArgumentParser):

    """
    A parser with only required toil args in --help with --help-toil option.

    Toil options are automatically added, but hidden by default in the help
    print. However, the `--help-toil` argument prints toil full rocketry.
    """

    def __init__(self, **kwargs):
        """Add Toil`--help-toil` to parser."""
        super().__init__(**kwargs)

        self.add_argument(
            "--help-toil",
            action=_ToilHelpAction,
            default=argparse.SUPPRESS,
            help="show help with toil arguments and exit",
        )

    @property
    def custom_actions(self):
        """List of custom actions for usage summary."""
        return CUSTOM_TOIL_ACTIONS if not self.show_toil_groups else []

    @property
    def show_toil_groups(self):
        """Whether toil help groups should be displayed."""
        return getattr(self, SHOW_TOILGROUPS_PROPERTY, False)

    def hide_action_group(self, action_group):
        """Determine if an action group should be hidden."""
        is_toil_group = action_group.title.lower().startswith("toil")
        if is_toil_group or "Logging Options" in action_group.title:
            return not self.show_toil_groups

        return False

    def get_help_groups(self):
        """Decide whether to show toil options or not."""
        action_groups = []
        actions = []

        for action_group in self._action_groups:
            if not self.hide_action_group(action_group):
                action_groups.append(action_group)
                actions += action_group._group_actions

        return actions, action_groups

    def format_help(self):
        """Include toil options if `self.show_toil_groups` is True."""
        formatter = self._get_formatter()

        # decide whether to show toil options or not
        actions, action_groups = self.get_help_groups()

        # usage, the CUSTOM_TOIL_ACTIONS are just for display
        formatter.add_usage(
            self.usage, actions + self.custom_actions, self._mutually_exclusive_groups
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
        if not self.show_toil_groups:
            formatter.start_section("toil arguments")
            formatter.add_arguments(CUSTOM_TOIL_ACTIONS)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()


class ContainerArgumentParser(ToilShortArgumentParser):

    """Toil Argument Parser with options for containerized system calls."""

    _ARGUMENT_GROUP_NAME = "container arguments"

    def __init__(self, *args, **kwargs):
        """Add container options to parser."""
        super().__init__(*args, **kwargs)
        settings = self.add_argument_group(self._ARGUMENT_GROUP_NAME)

        settings.add_argument(
            "--docker",
            help="name/path of the docker image available in daemon",
            default=None,
            required=False,
        )

        settings.add_argument(
            "--singularity",
            help="name/path of the singularity image available in deamon",
            default=None,
            required=False,
        )

        settings.add_argument(
            "--volumes",
            help="tuples of (local path, absolute container path)",
            required=False,
            default=None,
            action="append",
            nargs=2,
        )

        self.add_argument(
            "--help-container",
            action=_ContainerHelpAction,
            default=argparse.SUPPRESS,
            help="show help with container arguments and exit",
        )

    def hide_action_group(self, action_group):
        """Return falsey if group shouldn't be showed."""
        if action_group.title.startswith(self._ARGUMENT_GROUP_NAME):
            return not getattr(self, SHOW_CONTGROUPS_PROPERTY, False)

        return super().hide_action_group(action_group)

    def parse_args(self, args=None, namespace=None):
        """Validate parsed options."""
        args = super().parse_args(args=args, namespace=namespace)

        images = [args.docker, args.singularity]

        if all(images):
            raise click.UsageError("use --singularity or --docker, not both.")

        if args.volumes and not any(images):
            raise click.UsageError(
                "--volumes should be used only with " "--singularity or --docker."
            )

        if any(images):
            validate_kwargs = {}

            if args.volumes:
                validate_kwargs["volumes"] = args.volumes

            if args.workDir:
                validate_kwargs["working_dir"] = args.workDir

            if args.docker:
                validate_kwargs["image"] = args.docker
                validators.validate_docker(**validate_kwargs)
            else:
                validate_kwargs["image"] = args.singularity
                validators.validate_singularity(**validate_kwargs)

        return args
