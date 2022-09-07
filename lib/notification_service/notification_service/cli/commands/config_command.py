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
import yaml
from pygments.lexers.configs import IniLexer

from notification_service.settings import get_configuration_file_path, NOTIFICATION_HOME
from notification_service.util.cli import should_use_colors, get_terminal_formatter
from notification_service.util.server_config import create_server_config

logger = logging.getLogger(__name__)


def config_get_value(args):
    """Gets the option value of the configuration."""
    with open(get_configuration_file_path(), 'r') as f:
        yaml_config = yaml.load(f, Loader=yaml.FullLoader)
        if args.option not in yaml_config:
            raise SystemExit(f'The option [{args.option}] is not found in config.')
        value = yaml_config[args.option]
        print(value)


def config_init(args):
    """Initializes the default configuration."""
    if not os.path.exists(NOTIFICATION_HOME):
        os.makedirs(NOTIFICATION_HOME)
    config_file = NOTIFICATION_HOME + '/notification_server.yaml'
    if os.path.exists(config_file):
        logger.info('Notification server config has already initialized at {}.'.format(config_file))
    else:
        create_server_config(NOTIFICATION_HOME, {'NOTIFICATION_HOME': NOTIFICATION_HOME})
        logger.info('Notification server config generated at {}.'.format(config_file))


def config_list(args):
    """List all options of the configuration."""
    with open(get_configuration_file_path(), 'r') as f:
        code = f.read()
        if should_use_colors(args):
            code = pygments.highlight(code=code, formatter=get_terminal_formatter(), lexer=IniLexer())
        print(code)
