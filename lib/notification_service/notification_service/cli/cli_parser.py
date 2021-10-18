#!/usr/bin/env python
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
"""Command-line interface"""

import argparse
from argparse import Action, RawTextHelpFormatter
from functools import lru_cache

from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Union

from notification_service.util.utils import import_string, partition


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
        """Override error and use print_instead of print_usage"""
        self.print_help()
        self.exit(2, f'\n{self.prog} command error: {message}, see help above.\n')


class Arg:
    """Class to keep information about command line argument"""
    # Used in Arg to enable `None' as a distinct value from "not passed"
    _UNSET = object()

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
            if v is Arg._UNSET:
                continue
            if k in ("self", "flags"):
                continue

            self.kwargs[k] = v

    # pylint: enable=redefined-builtin,unused-argument,too-many-arguments

    def add_to_parser(self, parser: argparse.ArgumentParser):
        """Add this argument to an ArgumentParser"""
        parser.add_argument(*self.flags, **self.kwargs)


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


ARG_YES = Arg(
    ("-y", "--yes"), help="Do not prompt to confirm reset. Use with care!", action="store_true", default=False
)

ARG_DB_VERSION = Arg(
    ("-v", "--version"),
    help=(
        'The version corresponding to the database.'
    ),
    default='heads',
)


CLICommand = Union[ActionCommand, GroupCommand]

VERSION_COMMAND = ActionCommand("version",
                                "Shows the version of Notification.",
                                lazy_load_command("notification_service.cli.commands.version_command.version"),
                                [],
                                "Shows the version of Notification.")
DB_COMMANDS = (
    ActionCommand(
        name='init',
        help="Initialize the metadata database",
        func=lazy_load_command('notification_service.cli.commands.db_command.init'),
        args=(),
    ),
    ActionCommand(
        name='reset',
        help="Burn down and rebuild the metadata database",
        func=lazy_load_command('notification_service.cli.commands.db_command.reset'),
        args=(ARG_YES,),
    ),
    ActionCommand(
        name='upgrade',
        help="Upgrade the metadata database to the version",
        func=lazy_load_command('notification_service.cli.commands.db_command.upgrade'),
        args=(ARG_DB_VERSION,),
    ),
    ActionCommand(
        name='downgrade',
        help="Downgrade the metadata database to the version",
        func=lazy_load_command('notification_service.cli.commands.db_command.downgrade'),
        args=(ARG_DB_VERSION,),
    )
)

notification_commands: List[CLICommand] = [
    VERSION_COMMAND,
    GroupCommand(
        name='db',
        help="Database operations",
        subcommands=DB_COMMANDS,
    ),
]
ALL_COMMANDS_DICT: Dict[str, CLICommand] = {sp.name: sp for sp in notification_commands}


class NotificationHelpFormatter(argparse.HelpFormatter):
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
            parts.append("\n")
            parts.append('%*s%s:\n' % (self._current_indent, '', "Groups"))
            self._indent()
            for subaction in group_subcommands:
                parts.append(self._format_action(subaction))
            self._dedent()

            parts.append("\n")
            parts.append('%*s%s:\n' % (self._current_indent, '', "Commands"))
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
    parser = DefaultHelpParser(prog="notification", formatter_class=NotificationHelpFormatter)
    subparsers = parser.add_subparsers(dest='subcommand', metavar="GROUP_OR_COMMAND")
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

    positional, optional = partition(lambda x: x.flags[0].startswith("-"), args)
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
        raise ValueError("Invalid command definition.")


def _add_action_command(sub: ActionCommand, sub_proc: argparse.ArgumentParser) -> None:
    for arg in _sort_args(sub.args):
        arg.add_to_parser(sub_proc)
    sub_proc.set_defaults(func=sub.func)


def _add_group_command(sub: GroupCommand, sub_proc: argparse.ArgumentParser) -> None:
    subcommands = sub.subcommands
    sub_subparsers = sub_proc.add_subparsers(dest="subcommand", metavar="COMMAND")
    sub_subparsers.required = True

    for command in sorted(subcommands, key=lambda x: x.name):
        _add_command(sub_subparsers, command)
