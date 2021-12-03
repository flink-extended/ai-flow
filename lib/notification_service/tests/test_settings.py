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
import os
import unittest
import notification_service.settings

from notification_service.settings import get_configuration, get_configuration_file_path, get_notification_home


class TestSettings(unittest.TestCase):

    def test_get_configuration(self):
        notification_service.settings.NOTIFICATION_HOME = os.path.dirname(__file__)
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

        current_dir = os.path.dirname(__file__)
        self.assertEqual(os.path.join(current_dir, "notification_server.yaml"),
                         get_configuration_file_path(current_dir))


if __name__ == '__main__':
    unittest.main()
