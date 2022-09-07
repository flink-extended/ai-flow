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
import yaml

import logging
import os

from typing import Dict

logger = logging.getLogger(__name__)


class NotificationServerConfig(object):
    def __init__(self, config_file):
        self.config_file = config_file
        self._port = 50052
        self._db_uri = None
        self._enable_ha = False
        self._ha_ttl_ms = None
        self._advertised_uri = None
        self._wait_for_server_started_timeout = 5.0
        self._parse_config()

    def _parse_config(self):
        with open(self.config_file, 'r') as f:
            yaml_config = yaml.load(f, Loader=yaml.FullLoader)
            if 'server_port' in yaml_config:
                self._port = yaml_config['server_port']
            if 'db_uri' in yaml_config:
                self._db_uri = yaml_config['db_uri']
            if 'enable_ha' in yaml_config:
                self._enable_ha = yaml_config['enable_ha']
            if 'ha_ttl_ms' in yaml_config:
                self._ha_ttl_ms = yaml_config['ha_ttl_ms']
            if 'advertised_uri' in yaml_config:
                self._advertised_uri = yaml_config['advertised_uri']
            if 'wait_for_server_started_timeout' in yaml_config:
                self._wait_for_server_started_timeout = yaml_config['wait_for_server_started_timeout']

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        self._port = port

    @property
    def db_uri(self):
        return self._db_uri

    @db_uri.setter
    def db_uri(self, db_uri):
        self._db_uri = db_uri

    @property
    def enable_ha(self):
        return self._enable_ha

    @enable_ha.setter
    def enable_ha(self, enable_ha):
        self._enable_ha = enable_ha

    @property
    def ha_ttl_ms(self):
        return self._ha_ttl_ms

    @ha_ttl_ms.setter
    def ha_ttl_ms(self, ha_ttl_ms):
        self._ha_ttl_ms = ha_ttl_ms

    @property
    def advertised_uri(self):
        return self._advertised_uri

    @advertised_uri.setter
    def advertised_uri(self, advertised_uri):
        self._advertised_uri = advertised_uri

    @property
    def wait_for_server_started_timeout(self):
        return self._wait_for_server_started_timeout

    @wait_for_server_started_timeout.setter
    def wait_for_server_started_timeout(self, wait_for_server_started_timeout):
        self._wait_for_server_started_timeout = wait_for_server_started_timeout

    def __repr__(self):
        return f"""
port: {self.port}
db_uri: {self.db_uri}
        """


def create_server_config(root_dir_path, param: Dict[str, str]):
    """
    Generate the default config of the Notification Server.
    """
    import notification_service.config_templates
    default_config_file_name = 'default_notification_server.yaml'
    config_file_name = 'notification_server.yaml'

    if not os.path.exists(root_dir_path):
        logging.info('{} does not exist, creating the directory.'.format(root_dir_path))
        os.makedirs(root_dir_path, exist_ok=False)
    default_server_config_path = os.path.join(
        os.path.dirname(notification_service.config_templates.__file__), default_config_file_name
    )
    if not os.path.exists(default_server_config_path):
        raise Exception('Default notification server config is not found at {}.'.format(default_server_config_path))

    server_config_target_path = os.path.join(root_dir_path, config_file_name)
    with open(default_server_config_path, encoding='utf-8') as config_file:
        default_config = config_file.read().format(**param)
    with open(server_config_target_path, mode='w', encoding='utf-8') as f:
        f.write(default_config)
    return server_config_target_path
