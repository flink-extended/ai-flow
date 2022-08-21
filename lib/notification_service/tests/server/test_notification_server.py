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

from notification_service.client.embedded_notification_client import EmbeddedNotificationClient
from notification_service.model.event import Event, EventKey
from notification_service.server.server_runner import NotificationServerRunner
from notification_service.util import db
from notification_service.util.server_config import NotificationServerConfig

_SQLITE_FILE = 'ns.db'

config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util/notification_server.yaml')


class TestNotificationServer(unittest.TestCase):

    def _clean_db(self):
        if os.path.exists(_SQLITE_FILE):
            os.remove(_SQLITE_FILE)

    def setUp(self) -> None:
        self._clean_db()
        config = NotificationServerConfig(config_file)
        db.clear_engine_and_session()
        db.create_all_tables(config.db_uri)
        self.event_key = EventKey(name='a')

    def tearDown(self) -> None:
        self._clean_db()
        db.clear_engine_and_session()

    def test_run_notification_server(self):
        server = NotificationServerRunner(config_file=config_file)
        server.start()
        client = EmbeddedNotificationClient(server_uri='localhost:50052', namespace='default', sender='sender')
        client.send_event(Event(event_key=self.event_key, message='a'))
        self.assertEqual(1, len(client.list_events(name='a')))
        self.assertEqual('a', client.list_events(name='a')[0].message)
        server.stop()

    def test__wait_for_server_available(self):
        from grpc import FutureTimeoutError
        server = NotificationServerRunner(config_file=config_file)
        with self.assertRaises(FutureTimeoutError):
            server._wait_for_server_available(timeout=0.1)
        server.start()
        server._wait_for_server_available(timeout=0.1)
        server._wait_for_server_available(timeout=None)
        server.stop()

    def test_run_ha_notification_server(self):
        server1 = NotificationServerRunner(config_file=config_file)
        server1.config.port = 50053
        server1.config.enable_ha = True
        server1.config.advertised_uri = 'localhost:50053'
        server1.start()
        server2 = NotificationServerRunner(config_file=config_file)
        server2.config.port = 50054
        server2.config.enable_ha = True
        server2.config.advertised_uri = 'localhost:50054'
        server2.start()
        client = EmbeddedNotificationClient(server_uri='localhost:50053,localhost:50054',
                                            namespace='default',
                                            sender='sender')
        client.send_event(Event(event_key=self.event_key, message='b'))
        self.assertEqual(1, len(client.list_events(name='a')))
        self.assertEqual('b', client.list_events(name='a')[0].message)
        client.disable_high_availability()
        server1.stop()
        server2.stop()


if __name__ == '__main__':
    unittest.main()
