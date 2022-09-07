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
"""Config command"""
import logging
import os

import pygments
import yaml
from pygments.lexers.configs import IniLexer

from ai_flow.settings import get_configuration_file_path, AIFLOW_HOME
from ai_flow.util.cli_utils import should_use_colors, get_terminal_formatter
from ai_flow.util.config_utils import create_default_server_config

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
    if not os.path.exists(AIFLOW_HOME):
        os.makedirs(AIFLOW_HOME)
    config_file = AIFLOW_HOME + '/aiflow_server.yaml'
    if os.path.exists(config_file):
        logger.info('AIFlow server config has already initialized at {}.'.format(config_file))
    else:
        create_default_server_config(AIFLOW_HOME)
        logger.info('AIFlow server config generated at {}.'.format(config_file))


def config_list(args):
    """List all options of the configuration."""
    with open(get_configuration_file_path(), 'r') as f:
        code = f.read()
        if should_use_colors(args):
            code = pygments.highlight(code=code, formatter=get_terminal_formatter(), lexer=IniLexer())
        print(code)
