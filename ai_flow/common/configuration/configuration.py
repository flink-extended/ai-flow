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
from copy import deepcopy
from typing import Dict, Any

from .helpers import TRUTH_TEXT, FALSE_TEXT, get_aiflow_home, parameterized_config, write_default_config
from ai_flow.common.exception.exceptions import AIFlowConfigException
from ai_flow.common.util.file_util.yaml_utils import load_yaml_string
from ..env import expand_env_var

logger = logging.getLogger(__name__)


class Configuration(object):

    def __init__(self,
                 config_file: str):
        self._config: Dict[str, Any] = None
        self.reload(config_file)

    def reload(self, config_file):
        with open(config_file, encoding='utf-8') as fb:
            config_str = parameterized_config(fb.read())
        self._config = load_yaml_string(config_str)

    def get(self, key: str, fallback=None) -> Any:
        """
        Get the configuration values corresponding to :attr:`key`.
        :param key: key to retrieve
        :param fallback: default value in case the key is missing
        :return: the value found or a default
        """
        val = self._config.get(str(key).lower(), fallback)
        if val is not None:
            return val
        else:
            logger.warning("key [%s] not found in config", key)
            raise AIFlowConfigException(f"key [{key}] not found in config")

    def get_str(self, key, fallback=None) -> str:
        val = self._config.get(str(key).lower(), fallback)
        if val is not None:
            return expand_env_var(val)
        else:
            logger.warning("key [%s] not found in config", key)
            raise AIFlowConfigException(f"key [{key}] not found in config")

    def get_int(self, key, fallback=None) -> int:
        val = self.get_str(key, fallback=fallback)
        try:
            return int(val)
        except ValueError:
            raise AIFlowConfigException(
                f'Failed to convert value to int. Please check "{key}" key. '
                f'Current value: "{val}".'
            )

    def get_float(self, key, fallback=None) -> float:
        val = self.get_str(key, fallback=fallback)
        try:
            return float(val)
        except ValueError:
            raise AIFlowConfigException(
                f'Failed to convert value to float. Please check "{key}" key. '
                f'Current value: "{val}".'
            )

    def get_bool(self, key, fallback=False) -> bool:
        """
        Get the item value as a bool.

        :param key: key
        :param fallback: fallback value
        """
        val = self.get_str(key, fallback=fallback)
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        if s not in TRUTH_TEXT and s not in FALSE_TEXT:
            raise ValueError("Expected a valid True or False expression.")
        return s in TRUTH_TEXT

    def as_dict(self) -> dict:
        """Return the representation as a dictionary."""
        return deepcopy(self._config)

    def __eq__(self, other):
        """Equality operator."""
        return self.as_dict() == Configuration(other).as_dict()

    def __str__(self) -> str:
        return str({k: v for k, v in sorted(self.as_dict().items())})


def get_client_configuration():
    client_config_file_name = 'aiflow_client.yaml'
    home_dir = get_aiflow_home()
    config_path = os.path.join(home_dir, client_config_file_name)
    if not os.path.isfile(config_path):
        logger.warning("Client configuration file not found in {}, generating a default.".format(config_path))
        if not os.path.exists(home_dir):
            os.makedirs(home_dir)
        write_default_config('aiflow_client.yaml')
    config = Configuration(config_path)
    return config


def get_server_configuration():
    server_config_file_name = 'aiflow_server.yaml'
    config_path = os.path.join(get_aiflow_home(), server_config_file_name)
    if not os.path.isfile(config_path):
        logger.warning("Server configuration file not found in {}, using default.".format(config_path))
        config_path = os.path.join(os.path.dirname(__file__), 'config_templates', server_config_file_name)
    config = Configuration(config_path)
    return config
