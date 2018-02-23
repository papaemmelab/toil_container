"""toil_container pasers."""

import argparse

from toil.job import Job
import click

from toil_container import validators


CUSTOM_TOIL_ACTIONS = [
    argparse.Action(
        ["TOIL OPTIONAL ARGS"],
        dest="",
        default=argparse.SUPPRESS,
        help="see --help-toil for a full list of toil parameters",
        ),
    argparse.Action(
        [],
        dest="jobStore",
        help="the location of the job store for the workflow. "
        "See --help-toil for more information [REQUIRED]",
        ),
    ]


class _ToilHelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        """Print parser help and exist whilst adding a flag to the parser."""
        parser.show_toil_groups = True
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

        super(ToilBaseArgumentParser, self).__init__(**kwargs)

        if version:
            self.add_argument(
                "-v", "--version",
                action="version",
                version="%(prog)s " + str(version)
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
        super(ToilShortArgumentParser, self).__init__(**kwargs)

        self.add_argument(
            "--help-toil",
            action=_ToilHelpAction, default=argparse.SUPPRESS,
            help="print help with full list of Toil arguments and exit"
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


class ContainerArgumentParser(ToilShortArgumentParser):

    """Toil Argument Parser with options for containerized system calls."""

    def __init__(self, *args, **kwargs):
        """Add container options to parser."""
        super(ContainerArgumentParser, self).__init__(*args, **kwargs)
        settings = self.add_argument_group("container arguments")

        settings.add_argument(
            "--docker-image",
            help="name/path of the docker image available in daemon",
            default=None,
            required=False,
            )

        settings.add_argument(
            "--singularity-image",
            help="name/path of the singularity image available in deamon",
            default=None,
            required=False,
            )

        settings.add_argument(
            "--container-volumes",
            help="tuples of (local path, absolute container path)",
            required=False,
            default=None,
            action="append",
            nargs=2,
            )

    def parse_args(self, args=None, namespace=None):
        """Validate parsed options."""
        args = super(ContainerArgumentParser, self).parse_args(
            args=args, namespace=namespace
            )

        images = [args.docker_image, args.singularity_image]
        print(images)
        print(args.container_volumes, "SIGIFREDOOOOOO")

        if all(images):
            raise click.UsageError(
                "You can't pass both --singularity-image and --docker-image."
                )

        if args.container_volumes and not any(images):
            raise click.UsageError(
                "--container-volumes should be used only with "
                "--singularity_image or --docker-image."
                )

        if any(images):
            validate_kwargs = {}

            if args.container_volumes:
                validate_kwargs["volumes"] = args.container_volumes

            if args.workDir:
                validate_kwargs["working_dir"] = args.workDir

            if args.docker_image:
                validate_kwargs["image"] = args.docker_image
                validators.validate_docker_image(**validate_kwargs)
            else:
                validate_kwargs["image"] = args.singularity_image
                validators.validate_singularity_image(**validate_kwargs)

        return args
