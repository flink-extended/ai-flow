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
"""Utilities module for cli"""

import functools
import os
import sys
from typing import Callable, TypeVar, cast

from pygments.formatters.terminal import TerminalFormatter
from pygments.formatters.terminal256 import Terminal256Formatter

from ai_flow.context.project_context import init_project_context

T = TypeVar("T", bound=Callable)  # pylint: disable=invalid-name


def init_config(f: T) -> T:
    """
    Decorates function to execute function at the same time submitting init_config
    but in CLI context.

    :param f: function instance
    :return: wrapped function
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        """
        An wrapper for cli functions. It assumes to have Namespace instance
        at 1st positional argument

        :param args: Positional argument. It assumes to have Namespace instance
            at 1st positional argument
        :param kwargs: A passthrough keyword argument
        """
        init_project_context(args[0].project_path)
        return f(*args, **kwargs)

    return cast(T, wrapper)


def get_terminal_formatter(**opts):
    """Returns the best formatter available in the current terminal."""
    if '256' in os.environ.get('TERM', ''):
        formatter = Terminal256Formatter(**opts)
    else:
        formatter = TerminalFormatter(**opts)
    return formatter


class ColorMode:
    """Coloring modes. If `auto` is then automatically detected."""

    ON = "on"
    OFF = "off"
    AUTO = "auto"


def is_tty():
    """
    Checks if the standard output is connected (is associated with a terminal device) to a tty(-like)
    device.
    """
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


def is_terminal_support_colors() -> bool:
    """Try to determine if the current terminal supports colors."""
    if sys.platform == "win32":
        return False
    if not is_tty():
        return False
    if "COLORTERM" in os.environ:
        return True
    term = os.environ.get("TERM", "dumb").lower()
    if term in ("xterm", "linux") or "color" in term:
        return True
    return False


def should_use_colors(args) -> bool:
    """Processes arguments and decides whether to enable color in output"""
    if args.color == ColorMode.ON:
        return True
    if args.color == ColorMode.OFF:
        return False
    return is_terminal_support_colors()
