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
"""Config command"""
import logging
import os

import pygments
from pygments.lexers.configs import IniLexer

from ai_flow.common.configuration.configuration import get_server_configuration
from ai_flow.common.configuration.helpers import write_default_config, get_server_configuration_file_path
from ai_flow.common.configuration.helpers import AIFLOW_HOME
from ai_flow.common.util.cli_utils import should_use_colors, get_terminal_formatter

logger = logging.getLogger(__name__)


def config_get_value(args):
    """Gets the option value of the configuration."""
    config = get_server_configuration()
    if config.get(args.option) is None:
        raise SystemExit(f'The option [{args.option}] is not found in config.')
    value = config.get(args.option)
    print(value)


def config_init(args):
    """Initializes the default configuration."""
    if not os.path.exists(AIFLOW_HOME):
        os.makedirs(AIFLOW_HOME)
    write_default_config('aiflow_server.yaml')


def config_list(args):
    """List all options of the configuration."""
    with open(get_server_configuration_file_path(), 'r') as f:
        code = f.read()
        if should_use_colors(args):
            code = pygments.highlight(code=code, formatter=get_terminal_formatter(), lexer=IniLexer())
        print(code)
