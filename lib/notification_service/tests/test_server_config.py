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

from notification_service.server_config import NotificationServerConfig


class TestNotificationServerConfig(unittest.TestCase):

    def test_load_notification_server_config(self):
        config_file = os.path.join(os.path.dirname(__file__), 'notification_server.yaml')
        ns_config = NotificationServerConfig(config_file)
        self.assertEqual(50052, ns_config.port)
        self.assertEqual('127.0.0.1:50052', ns_config.advertised_uri)
        self.assertEqual('sqlite:///ns.db', ns_config.db_uri)
        self.assertFalse(ns_config.enable_ha)
        self.assertEqual(10000, ns_config.ha_ttl_ms)

    def test_get_wait_for_server_started_timeout(self):
        config_file = os.path.join(os.path.dirname(__file__), 'notification_server.yaml')
        ns_config = NotificationServerConfig(config_file)
        self.assertEqual(5.0, ns_config.wait_for_server_started_timeout)


if __name__ == '__main__':
    unittest.main()
