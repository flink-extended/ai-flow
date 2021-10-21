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

from notification_service.base_notification import BaseEvent
from notification_service.client import NotificationClient
from notification_service.master import NotificationServer

_SQLITE_FILE = 'ns.db'


class TestNotificationServer(unittest.TestCase):

    def _clean_db(self):
        if os.path.exists(_SQLITE_FILE):
            os.remove(_SQLITE_FILE)

    def setUp(self) -> None:
        self._clean_db()

    def tearDown(self) -> None:
        self._clean_db()

    def test_run_notification_server(self):
        server = NotificationServer(port=50051, db_conn='sqlite:///ns.db')
        server.start()
        client = NotificationClient(server_uri='localhost:50051')
        client.send_event(BaseEvent(key='a', value='a'))
        self.assertEqual(1, len(client.list_events(key='a')))
        self.assertEqual('a', client.list_events(key='a')[0].value)
        server.stop()
        if os.path.exists(_SQLITE_FILE):
            os.remove(_SQLITE_FILE)

    def test_run_ha_notification_server(self):
        server1 = NotificationServer(port=50052, db_conn='sqlite:///ns.db', enable_ha=True)
        server1.start()
        server2 = NotificationServer(port=50053, db_conn='sqlite:///ns.db', enable_ha=True)
        server2.start()
        client = NotificationClient(server_uri='localhost:50051,localhost:50052', enable_ha=True)
        client.send_event(BaseEvent(key='b', value='b'))
        self.assertEqual(1, len(client.list_events(key='b')))
        self.assertEqual('b', client.list_events(key='b')[0].value)
        server1.stop()
        server2.stop()
        if os.path.exists(_SQLITE_FILE):
            os.remove(_SQLITE_FILE)


if __name__ == '__main__':
    unittest.main()
