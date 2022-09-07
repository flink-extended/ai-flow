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
import logging
import os

from ai_flow.common.env import get_aiflow_home

logger = logging.getLogger(__name__)
TRUTH_TEXT = frozenset(("t", "true", "y", "yes", "on", "1"))
FALSE_TEXT = frozenset(("f", "false", "n", "no", "off", "0", ""))


# Set AIFLOW_HOME to local() to effect in `parameterized_config`
AIFLOW_HOME = get_aiflow_home()


def read_template_config_file(file_name: str) -> str:
    templates_dir = os.path.join(os.path.dirname(__file__), 'config_templates')
    file_path = os.path.join(templates_dir, file_name)
    with open(file_path, encoding='utf-8') as config_file:
        return config_file.read()


def parameterized_config(template):
    """
    Generates a configuration from the provided template + variables defined in
    current scope

    :param template: a config content templated with {{variables}}
    """
    all_vars = {k: v for d in [globals(), locals()] for k, v in d.items()}
    return template.format(**all_vars)


def write_default_config(file_name):
    """
    Generate default configuration file

    :param file_name: the file to be generated
    """
    config_str = read_template_config_file(file_name)
    default_config_path = os.path.join(get_aiflow_home(), file_name)
    if not os.path.isfile(default_config_path):
        logger.info('Creating new AIFlow config file in: %s', default_config_path)
        with open(default_config_path, 'w') as file:
            cfg = parameterized_config(config_str)
            file.write(cfg)
    else:
        logger.warning(f'Config {file_name} already exists at {default_config_path}')


def get_server_configuration_file_path():
    default_config_path = os.path.join(get_aiflow_home(), 'aiflow_server.yaml')
    if not os.path.exists(default_config_path):
        raise FileNotFoundError('Config file {} not found.'.format(default_config_path))
    return default_config_path
