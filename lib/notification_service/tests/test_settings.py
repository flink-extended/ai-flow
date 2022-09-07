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
import os
import unittest
from tempfile import TemporaryDirectory

import notification_service.settings

from notification_service.settings import get_configuration, get_configuration_file_path, get_notification_home


class TestSettings(unittest.TestCase):

    def setUp(self) -> None:
        self.config_str = """
server_port: 50052
# uri of database backend for notification server
db_uri: sqlite:///ns.db
# High availability is disabled by default
enable_ha: false
# TTL of the heartbeat of a server, i.e., if the server hasn't send heartbeat for the TTL time, it is down.
ha_ttl_ms: 10000
# Hostname and port the server will advertise to clients when HA enabled. If not set, it will use the local ip and configured port.
advertised_uri: 127.0.0.1:50052
"""

    def test_get_configuration(self):
        with TemporaryDirectory(prefix='test_config') as tmp_dir:
            temp_config_file = os.path.join(tmp_dir, 'notification_server.yaml')
            with open(temp_config_file, 'w') as f:
                f.write(self.config_str)
            notification_service.settings.NOTIFICATION_HOME = tmp_dir
            ns_config = get_configuration()
            self.assertEqual(50052, ns_config.port)
            self.assertEqual('127.0.0.1:50052', ns_config.advertised_uri)
            self.assertEqual('sqlite:///ns.db', ns_config.db_uri)
            self.assertFalse(ns_config.enable_ha)
            self.assertEqual(10000, ns_config.ha_ttl_ms)

    def test_get_notification_home(self):
        prev_home = os.environ['HOME']
        try:
            os.environ['HOME'] = "/home"
            self.assertEqual(os.path.join("/home", "notification_service"), get_notification_home())
            os.environ['NOTIFICATION_HOME'] = "/notification_home"
            self.assertEqual(os.path.join("/notification_home"), get_notification_home())

        finally:
            os.environ['HOME'] = prev_home
            if 'NOTIFICATION_HOME' in os.environ:
                del os.environ['NOTIFICATION_HOME']

    def test_get_configuration_path(self):
        with self.assertRaises(FileNotFoundError):
            get_configuration_file_path('/non_exist_dir')

        with TemporaryDirectory(prefix='test_config') as tmp_dir:
            temp_config_file = os.path.join(tmp_dir, 'notification_server.yaml')
            with open(temp_config_file, 'w') as f:
                f.write(self.config_str)
            self.assertEqual(temp_config_file, get_configuration_file_path(tmp_dir))


if __name__ == '__main__':
    unittest.main()
