"""toil_container utils."""

import os
import sys
import traceback
from functools import partial

import docker
import requests
import sentry_sdk
from sentry_sdk.integrations.logging import ignore_logger
from toil import subprocess
from toil.leader import FailedJobsException

from toil_container import exceptions


def check_output(**kwargs):
    return _call(check_output=True, **kwargs)


def check_call(**kwargs):
    return _call(check_output=False, **kwargs)


def _call(args, check_output, env=None, **kwargs):
    """
    Instead of calling subprocess.check_call directly,
    display standard error.

    Arguments:
        args (list): list of command line arguments passed to the tool.
        env (dict): environment variables to set inside container.
        check_output (bool): check_output or check_call behavior.
    
    Returns:
        int: 0 if call succeed else non-0.

    Raises:
        toil_container.SystemCallError: if the subprocess invocation fails.
    """
    command = args
    if check_output:
        call_function = subprocess.check_output
    else:
        call_function = subprocess.check_call

    try:
        output = call_function(command, env=env or {})
        error = False
    except (subprocess.CalledProcessError, OSError) as e:
        p = subprocess.Popen(command, env=env or {}, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        error = stderr.decode('ascii')
    
    if error:
        raise exceptions.SystemCallError(
            "The following error occurred:\n"
            "{}The command errored was: {}".format(str(error), " ".join(command))
        )
    
    return output


def get_errors_from_toil_logs(logs_toil):
    """
    Problem: For errors that occur outside Container system call, the exception
    to ContainerJob.Runner.startToil will always be toil.leader.FailedJobsException.
    Solution: Get useful error messages from logs_toil in the outdir.

    Arguments:
        logs_toil (str): Path to the Toil logs directory.

    Returns:
        dict: key as error message and value as traceback.
    """
    errors = {}

    # TODO: proper handle if there are lots of logs of the same exception    
    for fi in os.listdir(logs_toil):
        f = open(os.path.join(logs_toil, fi), 'r')
        content = f.readlines()
        tab_lines = [i for i in content if i.startswith('  ')]
        traceback_start_line = [i for i in content if i.startswith('Traceback')][0]
        traceback_start_index = content.index(traceback_start_line)
        error_message_index = content.index(tab_lines[-1]) + 1

        error_message = content[error_message_index].__str__()
        traceback = ''.join(content[traceback_start_index:error_message_index])

        if not error_message.startswith("toil_container.exceptions.SystemCallError:"):
            errors[error_message] = traceback

    return errors


def initialize_sentry(tool_name, tool_release, ignore_addition_error=[]):
    """
    Standardize sentry initialization to:
        1. ignore noisey logs from toil.worker
        2. set up the correct dsn
        3. custom logic to catch useful error message from toil
        4. custom grouping logic by resetting `fingerprint`
        5. set up tool version, environment

    Arguments:
        tool_name (str): name of the tool.
        tool_release (str): version of the tool.
        ignore_addition_error (list): a list of additional exceptions to be ignored.
    """

    dsn = get_sentry_dsn(tool_name)
    sentry_sdk.utils.MAX_STRING_LENGTH = 2048
    # when a toil job fails, toil.worker always log
    # "it logs exiting the worker because of a failed job"
    ignore_logger('toil.worker')
    sentry_sdk.init(
        dsn=dsn,
        release=tool_release,
        environment='production' if is_production_env() else 'non-production',
        before_send=partial(
            before_send_sentry_handler,
            ignore_addition_error=ignore_addition_error
        ),
    )


def get_sentry_dsn(tool_name):
    """ 
    Retrieve key and project_id from environmental variable,
    and create dsn.

    Arguments:
        tool_name (str): Name of the tool, the project ID should be in an
                         environ variable with name SENTRY_{tool_name}_KEY.
    
    Returns:
        str : properly formatted dsn

    Raises:
        SentryEnvironVarNotAvailableError: when required sentry environ variable is not found.
    """
    try:
        SENTRY_KEY = os.environ['SENTRY_KEY']
        PROJECT_ID = os.environ[f'SENTRY_{tool_name.upper()}_KEY']
    except KeyError as e:
        raise exceptions.SentryEnvironVarNotAvailableError(e)

    dsn = f'https://{SENTRY_KEY}@sentry.io/{PROJECT_ID}'
    return dsn


def before_send_sentry_handler(event, hint, ignore_addition_error):
    """
    Custom logic before sending the event to Sentry.

    Arguments:
        event (obj): the event to be sent to sentry.
        hint (dict): the hint to be sent to sentry.
        ignore_additional_error (list): a list of additional exceptions to be ignored.

    Returns:
        obj : modified event object to be sent to sentry.
    """
    # Ignore FailedJobsException b/c a failed toil jobs always results in FailedJobsException
    exceptions_to_be_ignored = [
        FailedJobsException,
        # exceptions.SystemCallError
    ]
    exceptions_to_be_ignored += [ignore_addition_error]
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if exc_type == exceptions.ContainerError:
            error_message = str(exc_value)
            useful_message = error_message.split('\n')[1]
            # replace the ContainerError title with the specific error
            event['exception']['values'][0]['type'] = useful_message
            event['fingerprint'] = [useful_message]
        if exc_type in exceptions_to_be_ignored:
            print(f'sentry: ignored exception: {exc_type}')
            return None
        print(f'sentry: report exception: {exc_type}')
    return event


def is_docker_available(raise_error=False, path=False):
    """
    Check if docker is available to run in the current environment.

    Arguments:
        raise_error (bool): flag to raise error when command is unavailable.
        path (bool): flag to return location of the command in the user's path.

    Returns:
        bool: True if docker is available.

    Raises:
        OSError: if the raise_error flag was passed as an argument and the
        command is not available to execute.
    """
    expected_exceptions = (requests.exceptions.ConnectionError, docker.errors.APIError)

    try:
        # Test docker is running
        client = docker.from_env()
        is_available = client.ping()

        if path:
            return which("docker")
        return is_available

    except expected_exceptions as error:
        if raise_error:
            raise exceptions.DockerNotAvailableError(str(error))
        return False


def is_singularity_available(raise_error=False, path=False):
    """
    Check if singularity is available to run in the current environment.

    Arguments:
        raise_error (bool): flag to raise error when command is unavailable.
        path (bool): flag to return location of the command in the user's path.

    Returns:
        bool: True if singularity is available.
        str: absolute location of the file in the user's path.

    Raises:
        OSError: if the raise_error flag was passed as an argument and the
        command is not available to execute.
    """
    try:
        subprocess.check_output(["singularity", "--version"])

        if path:
            return which("singularity")
        return True

    except (subprocess.CalledProcessError, OSError) as error:
        if raise_error:
            raise exceptions.SingularityNotAvailableError(str(error))
        return False


def get_container_error(error, command):
    """
    Return a ContainerError with information about `error` and
    the `command` that caused the error.
    """
    return exceptions.ContainerError(
        "The following error occurred in container:\n"
        "{}The command errored was: {}".format(str(error), " ".join(command))
    )


def is_production_env():
    """
    Return True if the tool is running in a production environment.
    """
    for i in sys.path:
        if ('python' in os.path.basename(i)) & ('production' in i):
            return True
    return False


def which(program):
    """
    Locate a program file in the user's path.

    Python implementation to mimic the behavior of the UNIX 'which' command
    And shutil.which() is not supported in python 2.x.

    See: https://stackoverflow.com/questions/377017

    Arguments:
        program (str): command to be tested. Can be relative or absolute path.

    Return:
        str: program file in the user's path.
    """
    fpath, _ = os.path.split(program)
    if fpath:
        if _is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if _is_exe(exe_file):
                return exe_file
    return None


def _is_exe(fpath):
    """
    Check if fpath is executable for the current user.

    Arguments:
        fpath (str): relative or absolute path.

    Return:
        bool: True if execution is granted, else False.
    """
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
