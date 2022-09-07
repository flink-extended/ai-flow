#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
"""Command-line interface"""

import argparse
from argparse import Action, RawTextHelpFormatter
from functools import lru_cache
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Union

from ai_flow.common.module_load import import_string
from ai_flow.util.cli_utils import ColorMode
from ai_flow.util.helpers import partition


def lazy_load_command(import_path: str) -> Callable:
    """Create a lazy loader for command"""
    _, _, name = import_path.rpartition('.')

    def command(*args, **kwargs):
        func = import_string(import_path)
        return func(*args, **kwargs)

    command.__name__ = name

    return command


class DefaultHelpParser(argparse.ArgumentParser):
    """CustomParser to display help message"""

    def error(self, message):
        """Override error and use print_help instead of print_usage"""
        self.print_help()
        self.exit(2, f'\n{self.prog} command error: {message}, see help above.\n')


# Used in Arg to enable `None' as a distinct value from "not passed"
_UNSET = object()


class Arg:
    """Class to keep information about command line argument"""

    # pylint: disable=redefined-builtin,unused-argument,too-many-arguments
    def __init__(
            self,
            flags=_UNSET,
            help=_UNSET,
            action=_UNSET,
            default=_UNSET,
            nargs=_UNSET,
            type=_UNSET,
            choices=_UNSET,
            required=_UNSET,
            metavar=_UNSET,
            dest=_UNSET,
    ):
        self.flags = flags
        self.kwargs = {}
        for k, v in locals().items():
            if v is _UNSET:
                continue
            if k in ('self', 'flags'):
                continue

            self.kwargs[k] = v

    # pylint: enable=redefined-builtin,unused-argument,too-many-arguments

    def add_to_parser(self, parser: argparse.ArgumentParser):
        """Add this argument to an ArgumentParser"""
        parser.add_argument(*self.flags, **self.kwargs)


# Shared
ARG_PROJECT_PATH = Arg(('project_path',), help='The path of the project')
ARG_WORKFLOW_NAME = Arg(('workflow_name',), help='The name of the workflow')
ARG_WORKFLOW_EXECUTION_ID = Arg(('workflow_execution_id',), help='The id of the workflow execution')
ARG_JOB_NAME = Arg(('job_name',), help='The name of the job')
ARG_OPTION = Arg(('option',), help='The option name of the configuration', )

ARG_DB_VERSION = Arg(
    ("-v", "--version"),
    help=(
        'The version corresponding to the database'
    ),
    default='heads',
)
ARG_CONTEXT = Arg(('-c', '--context'), help='The context of the workflow execution to start')

ARG_YES = Arg(
    ('-y', '--yes'), help='Do not prompt to confirm reset. Use with care!', action='store_true', default=False
)
ARG_OUTPUT = Arg(
    (
        '-o',
        '--output',
    ),
    help='Output format. Allowed values: json, yaml, table (default: table)',
    metavar='(table, json, yaml)',
    choices=('table', 'json', 'yaml'),
    default='table',
)
ARG_COLOR = Arg(
    ('--color',),
    help="Does emit colored config output (default: auto)",
    choices={ColorMode.ON, ColorMode.OFF, ColorMode.AUTO},
    default=ColorMode.AUTO,
)

ARG_SERVER_DAEMON = Arg(
    ("-d", "--daemon"),
    help="Daemonizes instead of running in the foreground",
    action="store_true"
)


class ActionCommand(NamedTuple):
    """Single CLI command"""

    name: str
    help: str
    func: Callable
    args: Iterable[Arg]
    description: Optional[str] = None
    epilog: Optional[str] = None


class GroupCommand(NamedTuple):
    """ClI command with subcommands"""

    name: str
    help: str
    subcommands: Iterable
    description: Optional[str] = None
    epilog: Optional[str] = None


CLICommand = Union[ActionCommand, GroupCommand]

DB_COMMANDS = (
    ActionCommand(
        name='init',
        help="Initializes the metadata database",
        func=lazy_load_command('ai_flow.cli.commands.db_command.init'),
        args=(),
    ),
    ActionCommand(
        name='reset',
        help="Burns down and rebuild the metadata database",
        func=lazy_load_command('ai_flow.cli.commands.db_command.reset'),
        args=(ARG_YES,),
    ),
    ActionCommand(
        name='upgrade',
        help="Upgrades the metadata database to the version",
        func=lazy_load_command('ai_flow.cli.commands.db_command.upgrade'),
        args=(ARG_DB_VERSION,),
    ),
    ActionCommand(
        name='downgrade',
        help="Downgrades the metadata database to the version",
        func=lazy_load_command('ai_flow.cli.commands.db_command.downgrade'),
        args=(ARG_DB_VERSION,),
    )
)

WORKFLOW_COMMANDS = (
    ActionCommand(
        name='delete',
        help='Deletes all DB records related to the specified workflow.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.workflow_delete'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_NAME, ARG_YES),
    ),
    ActionCommand(
        name='list',
        help='Lists all the workflows.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.workflow_list'),
        args=(ARG_PROJECT_PATH, ARG_OUTPUT),
    ),
    ActionCommand(
        name='list-executions',
        help='Lists all workflow executions of the workflow by workflow name.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.workflow_list_executions'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_NAME, ARG_OUTPUT),
    ),
    ActionCommand(
        name='pause-scheduling',
        help='Pauses a workflow scheduling.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.worfklow_pause_scheduling'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_NAME),
    ),
    ActionCommand(
        name='resume-scheduling',
        help='Resumes a paused workflow scheduling.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.worfklow_resume_scheduling'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_NAME),
    ),
    ActionCommand(
        name='show',
        help='Shows the workflow by workflow name.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.workflow_show'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_NAME, ARG_OUTPUT),
    ),
    ActionCommand(
        name='show-execution',
        help='Shows the workflow execution by workflow execution id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.workflow_show_execution'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_EXECUTION_ID, ARG_OUTPUT),
    ),
    ActionCommand(
        name='start-execution',
        help='Starts a new workflow execution by workflow name.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.workflow_start_execution'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_NAME, ARG_CONTEXT),
    ),
    ActionCommand(
        name='stop-execution',
        help='Stops the workflow execution by workflow execution id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.workflow_stop_execution'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_EXECUTION_ID),
    ),
    ActionCommand(
        name='stop-executions',
        help='Stops all workflow executions by workflow name.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.workflow_stop_executions'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_NAME),
    ),
    ActionCommand(
        name='submit',
        help='Submits the workflow by workflow name.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.workflow_submit'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_NAME),
    )
)

JOB_COMMANDS = (
    ActionCommand(
        name='list-executions',
        help='Lists all job executions of the workflow execution by workflow execution id.',
        func=lazy_load_command('ai_flow.cli.commands.job_command.job_list_executions'),
        args=(ARG_PROJECT_PATH, ARG_WORKFLOW_EXECUTION_ID, ARG_OUTPUT),
    ),
    ActionCommand(
        name='restart-execution',
        help='Restarts the job execution by job name and workflow execution id.',
        func=lazy_load_command('ai_flow.cli.commands.job_command.job_restart_execution'),
        args=(ARG_PROJECT_PATH, ARG_JOB_NAME, ARG_WORKFLOW_EXECUTION_ID),
    ),
    ActionCommand(
        name='show-execution',
        help='Shows the job execution by job name and workflow execution id.',
        func=lazy_load_command('ai_flow.cli.commands.job_command.job_show_execution'),
        args=(ARG_PROJECT_PATH, ARG_JOB_NAME, ARG_WORKFLOW_EXECUTION_ID, ARG_OUTPUT),
    ),
    ActionCommand(
        name='start-execution',
        help='Starts the job execution by job name and workflow execution id.',
        func=lazy_load_command('ai_flow.cli.commands.job_command.job_start_execution'),
        args=(ARG_PROJECT_PATH, ARG_JOB_NAME, ARG_WORKFLOW_EXECUTION_ID),
    ),
    ActionCommand(
        name='stop-execution',
        help='Stops the job execution by job name and workflow execution id.',
        func=lazy_load_command('ai_flow.cli.commands.job_command.job_stop_execution'),
        args=(ARG_PROJECT_PATH, ARG_JOB_NAME, ARG_WORKFLOW_EXECUTION_ID),
    ),
    ActionCommand(
        name='stop-scheduling',
        help='Stops scheduling the job by job name and workflow execution id.',
        func=lazy_load_command('ai_flow.cli.commands.job_command.job_stop_scheduling'),
        args=(ARG_PROJECT_PATH, ARG_JOB_NAME, ARG_WORKFLOW_EXECUTION_ID),
    ),
    ActionCommand(
        name='resume-scheduling',
        help='Resumes scheduling the job by job name and workflow execution id.',
        func=lazy_load_command('ai_flow.cli.commands.job_command.job_resume_scheduling'),
        args=(ARG_PROJECT_PATH, ARG_JOB_NAME, ARG_WORKFLOW_EXECUTION_ID),
    )
)

SERVER_COMMANDS = (
    ActionCommand("start",
                  "Starts the AIFlow server",
                  lazy_load_command("ai_flow.cli.commands.server_command.server_start"),
                  [ARG_SERVER_DAEMON],
                  "Starts the AIFlow server"),
    ActionCommand("stop",
                  "Stops the AIFlow server",
                  lazy_load_command("ai_flow.cli.commands.server_command.server_stop"),
                  [],
                  "Stops the AIFlow server"),
)

WEBSERVER_COMMANDS = (
    ActionCommand("start",
                  "Starts the AIFlow Webserver",
                  lazy_load_command("ai_flow.cli.commands.webserver_command.webserver_start"),
                  [ARG_SERVER_DAEMON],
                  "Starts the AIFlow Webserver"),
    ActionCommand("stop",
                  "Stops the AIFlow Webserver",
                  lazy_load_command("ai_flow.cli.commands.webserver_command.webserver_stop"),
                  [],
                  "Stops the AIFlow Webserver"),
)

CONFIG_COMMANDS = (
    ActionCommand(
        name='get-value',
        help='Gets the option value of the configuration.',
        func=lazy_load_command('ai_flow.cli.commands.config_command.config_get_value'),
        args=(ARG_OPTION,),
    ),
    ActionCommand(
        name='init',
        help='Initializes the default configuration.',
        func=lazy_load_command('ai_flow.cli.commands.config_command.config_init'),
        args=(),
    ),
    ActionCommand(
        name='list',
        help='List all options of the configuration.',
        func=lazy_load_command('ai_flow.cli.commands.config_command.config_list'),
        args=(ARG_COLOR,),
    ),
)

ai_flow_commands: List[CLICommand] = [
    ActionCommand(
        name='version',
        help="Shows the version",
        func=lazy_load_command('ai_flow.cli.commands.version_command.version'),
        args=(),
    ),
    GroupCommand(
        name='db',
        help="Database operations",
        subcommands=DB_COMMANDS,
    ),
    GroupCommand(
        name='server',
        help='AIFlow server operations',
        subcommands=SERVER_COMMANDS
    ),
    GroupCommand(
        name='webserver',
        help='AIFlow Webserver operations',
        subcommands=WEBSERVER_COMMANDS
    ),
    GroupCommand(
        name='workflow',
        help='Manages workflows of the given project',
        subcommands=WORKFLOW_COMMANDS,
    ),
    GroupCommand(
        name='job',
        help='Manages jobs of the given project',
        subcommands=JOB_COMMANDS,
    ),
    GroupCommand(
        name="config",
        help='Manage configuration',
        subcommands=CONFIG_COMMANDS
    ),
]
ALL_COMMANDS_DICT: Dict[str, CLICommand] = {sp.name: sp for sp in ai_flow_commands}


class AIFlowHelpFormatter(argparse.HelpFormatter):
    """
    Custom help formatter to display help message.

    It displays simple commands and groups of commands in separate sections.
    """

    def _format_action(self, action: Action):
        if isinstance(action, argparse._SubParsersAction):  # pylint: disable=protected-access

            parts = []
            action_header = self._format_action_invocation(action)
            action_header = '%*s%s\n' % (self._current_indent, '', action_header)
            parts.append(action_header)

            self._indent()
            subactions = action._get_subactions()  # pylint: disable=protected-access
            action_subcommands, group_subcommands = partition(
                lambda d: isinstance(ALL_COMMANDS_DICT[d.dest], GroupCommand), subactions
            )
            parts.append('\n')
            parts.append('%*s%s:\n' % (self._current_indent, '', 'Groups'))
            self._indent()
            for subaction in group_subcommands:
                parts.append(self._format_action(subaction))
            self._dedent()

            parts.append('\n')
            parts.append('%*s%s:\n' % (self._current_indent, '', 'Commands'))
            self._indent()

            for subaction in action_subcommands:
                parts.append(self._format_action(subaction))
            self._dedent()
            self._dedent()

            # return a single string
            return self._join_parts(parts)

        return super()._format_action(action)


@lru_cache(maxsize=None)
def get_parser() -> argparse.ArgumentParser:
    """Creates and returns command line argument parser"""
    parser = DefaultHelpParser(prog='aiflow', formatter_class=AIFlowHelpFormatter)
    subparsers = parser.add_subparsers(dest='subcommand', metavar='GROUP_OR_COMMAND')
    subparsers.required = True

    sub_name: str
    for sub_name in sorted(ALL_COMMANDS_DICT.keys()):
        sub: CLICommand = ALL_COMMANDS_DICT[sub_name]
        _add_command(subparsers, sub)
    return parser


def _sort_args(args: Iterable[Arg]) -> Iterable[Arg]:
    """Sort subcommand optional args, keep positional args"""

    def get_long_option(arg: Arg):
        """Get long option from Arg.flags"""
        return arg.flags[0] if len(arg.flags) == 1 else arg.flags[1]

    positional, optional = partition(lambda x: x.flags[0].startswith('-'), args)
    yield from positional
    yield from sorted(optional, key=lambda x: get_long_option(x).lower())


def _add_command(
        subparsers: argparse._SubParsersAction, sub: CLICommand  # pylint: disable=protected-access
) -> None:
    sub_proc = subparsers.add_parser(
        sub.name, help=sub.help, description=sub.description or sub.help, epilog=sub.epilog
    )
    sub_proc.formatter_class = RawTextHelpFormatter

    if isinstance(sub, GroupCommand):
        _add_group_command(sub, sub_proc)
    elif isinstance(sub, ActionCommand):
        _add_action_command(sub, sub_proc)
    else:
        raise Exception('Invalid command definition.')


def _add_action_command(sub: ActionCommand, sub_proc: argparse.ArgumentParser) -> None:
    for arg in _sort_args(sub.args):
        arg.add_to_parser(sub_proc)
    sub_proc.set_defaults(func=sub.func)


def _add_group_command(sub: GroupCommand, sub_proc: argparse.ArgumentParser) -> None:
    subcommands = sub.subcommands
    sub_subparsers = sub_proc.add_subparsers(dest='subcommand', metavar='COMMAND')
    sub_subparsers.required = True

    for command in sorted(subcommands, key=lambda x: x.name):
        _add_command(sub_subparsers, command)
