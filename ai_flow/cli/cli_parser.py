#
# Copyright 2022 The AI Flow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
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
from itertools import filterfalse, tee
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Union

from ai_flow.common.util.cli_utils import ColorMode
from ai_flow.common.util.module_utils import import_string


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

    def add_to_parser(self, parser: argparse.ArgumentParser):
        """Add this argument to an ArgumentParser"""
        parser.add_argument(*self.flags, **self.kwargs)


ARG_NAMESPACE_NAME = Arg(('namespace_name',), help='The name of the namespace')
ARG_WORKFLOW_NAME = Arg(('workflow_name',), help='The name of the workflow')
ARG_WORKFLOW_EXECUTION_ID = Arg(('workflow_execution_id',), help='The id of the workflow execution')
ARG_WORKFLOW_SCHEDULE_EXPRESSION = Arg(('expression',), help='The expression of the workflow schedule')
ARG_WORKFLOW_SCHEDULE_ID = Arg(('workflow_schedule_id',), help='The id of the workflow schedule')
ARG_WORKFLOW_TRIGGER_ID = Arg(('workflow_trigger_id',), help='The id of the workflow trigger')
ARG_TASK_EXECUTION_ID = Arg(('task_execution_id',), help='The id of the task execution')
ARG_TASK_NAME = Arg(('task_name',), help='The name of the task')
ARG_SEQUENCE_NUM = Arg(('sequence_number',), help='The sequence number of the task execution')
ARG_OPTION = Arg(('option',), help='The option name of the configuration', )
ARG_FILE_PATH = Arg(('file_path',), help='The path of the workflow file')
ARG_WORKFLOW_NAME = Arg(('workflow_name',), help='The name of workflow')
ARG_WORKFLOW_SNAPSHOT_PATH = Arg(('snapshot_path',), help='The path of code snapshot')
ARG_NOTIFICATION_SERVER_URI = Arg(('notification_server_uri',), help='The notification server to send events')
ARG_AIFLOW_SERVER_URI = Arg(('server_uri',), help='The aiflow server to send heartbeat')

ARG_DB_VERSION = Arg(
    ("-v", "--version"),
    help='The version corresponding to the database',
    default='heads',
)
ARG_YES = Arg(
    ('-y', '--yes'),
    help='Do not prompt to confirm reset. Use with care!',
    action='store_true',
    default=False
)
ARG_OUTPUT = Arg(
    ('-o', '--output'),
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
OPTION_FILES = Arg(
    ("-f", "--files"),
    help="Comma separated paths of files that would be uploaded along with the workflow",
)
OPTION_NAMESPACE = Arg(
    ("-n", "--namespace"),
    help="Namespace that contains the workflow",
)
OPTION_PROPERTIES = Arg(
    ("--properties",),
    help="Properties of namespace, which is a string in json format",
)
OPTION_HEARTBEAT_INTERVAL = Arg(
    ("--heartbeat-interval",),
    help="Interval in seconds that the task send heartbeat to scheduler"
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
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.delete_workflow'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE, ARG_YES),
    ),
    ActionCommand(
        name='list',
        help='Lists all the workflows.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.list_workflow'),
        args=(OPTION_NAMESPACE, ARG_OUTPUT,),
    ),
    ActionCommand(
        name='disable',
        help='Disables the workflow so that no more executions would be scheduled.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.disable_workflow'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE,),
    ),
    ActionCommand(
        name='enable',
        help='Enables the workflow which is disabled before.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.enable_workflow'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE,),
    ),
    ActionCommand(
        name='show',
        help='Shows the details of the workflow by workflow name.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.show_workflow'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE, ARG_OUTPUT,),
    ),
    ActionCommand(
        name='upload',
        help='Upload the workflow to the server along with artifacts.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_command.upload_workflows'),
        args=(ARG_FILE_PATH, OPTION_FILES,),
    )
)

WORKFLOW_SCHEDULE_COMMANDS = (
    ActionCommand(
        name='add',
        help='Creates a new schedule for workflow.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_schedule_command.add_workflow_schedule'),
        args=(ARG_WORKFLOW_NAME, ARG_WORKFLOW_SCHEDULE_EXPRESSION, OPTION_NAMESPACE,),
    ),
    ActionCommand(
        name='delete',
        help='Deletes the workflow schedule by id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_schedule_command.delete_workflow_schedule'),
        args=(ARG_WORKFLOW_SCHEDULE_ID, ARG_YES,),
    ),
    ActionCommand(
        name='delete-all',
        help='Deletes all schedules of the workflow.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_schedule_command.delete_workflow_schedules'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE, ARG_YES,),
    ),
    ActionCommand(
        name='show',
        help='Shows the details of the workflow schedule by id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_schedule_command.show_workflow_schedule'),
        args=(ARG_WORKFLOW_SCHEDULE_ID, ARG_OUTPUT,),
    ),
    ActionCommand(
        name='list',
        help='Lists all schedules of the workflow.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_schedule_command.list_workflow_schedules'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE, ARG_OUTPUT,),
    ),
    ActionCommand(
        name='pause',
        help='Pauses the schedule and the workflow would not periodically execute anymore.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_schedule_command.pause_workflow_schedule'),
        args=(ARG_WORKFLOW_SCHEDULE_ID,),
    ),
    ActionCommand(
        name='resume',
        help='Resumes the schedule which is paused before.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_schedule_command.resume_workflow_schedule'),
        args=(ARG_WORKFLOW_SCHEDULE_ID,),
    ),
)

WORKFLOW_TRIGGER_COMMANDS = (
    ActionCommand(
        name='delete',
        help='Deletes the workflow event trigger by id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_trigger_command.delete_workflow_trigger'),
        args=(ARG_WORKFLOW_TRIGGER_ID, ARG_YES,),
    ),
    ActionCommand(
        name='delete-all',
        help='Deletes all event triggers of the workflow.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_trigger_command.delete_workflow_triggers'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE, ARG_YES,),
    ),
    ActionCommand(
        name='show',
        help='Shows the details of the workflow event trigger by id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_trigger_command.show_workflow_trigger'),
        args=(ARG_WORKFLOW_TRIGGER_ID, ARG_OUTPUT,),
    ),
    ActionCommand(
        name='list',
        help='Lists all event triggers of the workflow.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_trigger_command.list_workflow_triggers'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE, ARG_OUTPUT,),
    ),
    ActionCommand(
        name='pause',
        help='Pauses the event trigger by id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_trigger_command.pause_workflow_trigger'),
        args=(ARG_WORKFLOW_TRIGGER_ID,),
    ),
    ActionCommand(
        name='resume',
        help='Resumes the event trigger by id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_trigger_command.resume_workflow_trigger'),
        args=(ARG_WORKFLOW_TRIGGER_ID,),
    ),
)

WORKFLOW_EXECUTION_COMMANDS = (
    ActionCommand(
        name='list',
        help='Lists all workflow executions of the workflow.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_execution_command.list_workflow_executions'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE, ARG_OUTPUT),
    ),
    ActionCommand(
        name='show',
        help='Shows the details of the workflow execution by execution id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_execution_command.show_workflow_execution'),
        args=(ARG_WORKFLOW_EXECUTION_ID, ARG_OUTPUT),
    ),
    ActionCommand(
        name='start',
        help='Starts a new execution of the workflow.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_execution_command.start_workflow_execution'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE),
    ),
    ActionCommand(
        name='stop',
        help='Stops the workflow execution by execution id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_execution_command.stop_workflow_execution'),
        args=(ARG_WORKFLOW_EXECUTION_ID,),
    ),
    ActionCommand(
        name='stop-all',
        help='Stops all workflow executions of the workflow.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_execution_command.stop_workflow_executions'),
        args=(ARG_WORKFLOW_NAME, OPTION_NAMESPACE, ARG_YES,),
    ),
    ActionCommand(
        name='delete',
        help='Deletes the workflow execution by execution id.',
        func=lazy_load_command('ai_flow.cli.commands.workflow_execution_command.delete_workflow_execution'),
        args=(ARG_WORKFLOW_EXECUTION_ID, ARG_YES,),
    ),
)

TASK_EXECUTION_COMMANDS = (
    ActionCommand(
        name='list',
        help='Lists all task executions of the workflow execution.',
        func=lazy_load_command('ai_flow.cli.commands.task_execution_command.list_task_executions'),
        args=(ARG_WORKFLOW_EXECUTION_ID, ARG_OUTPUT,),
    ),
    ActionCommand(
        name='show',
        help='Shows the details of the task execution by execution id.',
        func=lazy_load_command('ai_flow.cli.commands.task_execution_command.show_task_execution'),
        args=(ARG_TASK_EXECUTION_ID, ARG_OUTPUT,),
    ),
    ActionCommand(
        name='start',
        help='Starts a new execution of the task of the workflow execution.',
        func=lazy_load_command('ai_flow.cli.commands.task_execution_command.start_task_execution'),
        args=(ARG_WORKFLOW_EXECUTION_ID, ARG_TASK_NAME,),
    ),
    ActionCommand(
        name='stop',
        help='Stops the task execution by execution id.',
        func=lazy_load_command('ai_flow.cli.commands.task_execution_command.stop_task_execution'),
        args=(ARG_WORKFLOW_EXECUTION_ID, ARG_TASK_NAME,),
    ),
)

TASK_MANAGER_COMMANDS = (
    ActionCommand(
        name='run',
        help='Run the task manager for specific task execution on the worker.',
        func=lazy_load_command('ai_flow.cli.commands.task_manager_command.run_task_manager'),
        args=(ARG_WORKFLOW_NAME, ARG_WORKFLOW_EXECUTION_ID, ARG_TASK_NAME, ARG_SEQUENCE_NUM, ARG_WORKFLOW_SNAPSHOT_PATH,
              ARG_NOTIFICATION_SERVER_URI, ARG_AIFLOW_SERVER_URI, OPTION_HEARTBEAT_INTERVAL)
    ),
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

NAMESPACE_COMMANDS = (
    ActionCommand(
        name='add',
        help='Creates a namespace with specific name.',
        func=lazy_load_command('ai_flow.cli.commands.namespace_command.add_namespace'),
        args=(ARG_NAMESPACE_NAME, OPTION_PROPERTIES,),
    ),
    ActionCommand(
        name='delete',
        help='Deletes a namespace with specific name.',
        func=lazy_load_command('ai_flow.cli.commands.namespace_command.delete_namespace'),
        args=(ARG_NAMESPACE_NAME, ARG_YES,),
    ),
    ActionCommand(
        name='list',
        help='Lists all the namespaces.',
        func=lazy_load_command('ai_flow.cli.commands.namespace_command.list_namespaces'),
        args=(ARG_OUTPUT,),
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
        help='Workflow related operations',
        subcommands=WORKFLOW_COMMANDS,
    ),
    GroupCommand(
        name='workflow-schedule',
        help='Manages the periodic schedules of the workflow',
        subcommands=WORKFLOW_SCHEDULE_COMMANDS,
    ),
    GroupCommand(
        name='workflow-trigger',
        help='Manages the event triggers of the workflow',
        subcommands=WORKFLOW_TRIGGER_COMMANDS,
    ),
    GroupCommand(
      name='namespace',
      help='Namespace related operations',
      subcommands=NAMESPACE_COMMANDS,
    ),
    GroupCommand(
        name='workflow-execution',
        help='Workflow execution related operations',
        subcommands=WORKFLOW_EXECUTION_COMMANDS,
    ),
    GroupCommand(
        name='task-execution',
        help='Task execution related operations',
        subcommands=TASK_EXECUTION_COMMANDS,
    ),
    GroupCommand(
        name='taskmanager',
        help='Starts a taskmanager to execute a task execution',
        subcommands=TASK_MANAGER_COMMANDS,
    ),
    GroupCommand(
        name="config",
        help='Manages configuration',
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


def partition(pred: Callable, iterable: Iterable):
    """Use a predicate to partition entries into false entries and true entries"""
    iter_1, iter_2 = tee(iterable)
    return filterfalse(pred, iter_1), filter(pred, iter_2)


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
