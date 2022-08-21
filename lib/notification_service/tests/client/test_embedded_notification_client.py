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
import time
import unittest
from typing import List
from datetime import datetime

from notification_service.storage.alchemy.db_event_storage import DbEventStorage
from notification_service.client.notification_client import ListenerProcessor
from notification_service.server.server import NotificationServer
from notification_service.rpc.service import NotificationService
from notification_service.util import db
from notification_service.util.db import SQL_ALCHEMY_DB_FILE
from notification_service.model.event import Event, EventKey
from notification_service.client.embedded_notification_client import EmbeddedNotificationClient


class TestGrpcNotificationClient(unittest.TestCase):

    @classmethod
    def wait_for_master_started(cls, server_uri="localhost:50051"):
        last_exception = None
        for i in range(60):
            try:
                return EmbeddedNotificationClient(server_uri=server_uri, namespace='default', sender='sender')
            except Exception as e:
                time.sleep(2)
                last_exception = e
        raise Exception("The server %s is unavailable." % server_uri) from last_exception

    @classmethod
    def setUpClass(cls):
        db.create_all_tables()
        cls.storage = DbEventStorage()
        cls.master = NotificationServer(NotificationService(cls.storage))
        cls.master.run()
        cls.wait_for_master_started("localhost:50051")

    @classmethod
    def tearDownClass(cls):
        cls.master.stop()
        if os.path.exists(SQL_ALCHEMY_DB_FILE):
            os.remove(SQL_ALCHEMY_DB_FILE)

    def setUp(self):
        db.prepare_db()
        self.storage.clean_up()
        self.client = EmbeddedNotificationClient(server_uri="localhost:50051",
                                                 namespace='default',
                                                 sender='sender')

    def tearDown(self):
        db.clear_engine_and_session()

    def test_send_event(self):
        event = self.client.send_event(Event(event_key=EventKey(name='name_1'),
                                             message='message_1'))
        self.assertTrue(event.offset >= 1)

    def test_register_listener(self):
        class Counter(ListenerProcessor):
            def __init__(self):
                self.counter = 0

            def process(self, events: List[Event]):
                self.counter += len(events)
        processor = Counter()
        l_id = self.client.register_listener(listener_processor=processor)
        self.assertEqual(1, len(self.client.threads))
        for i in range(3):
            event = self.client.send_event(Event(event_key=EventKey(name='name_{}'.format(i)),
                                                 message='message_{}'.format(i)))
        self.client.unregister_listener(l_id)
        self.assertEqual(3, processor.counter)
        self.assertEqual(0, len(self.client.threads))

    def test_register_listener_with_offset(self):
        class Counter(ListenerProcessor):
            def __init__(self):
                self.counter = 0

            def process(self, events: List[Event]):
                self.counter += len(events)
        processor = Counter()
        l_id = self.client.register_listener(listener_processor=processor, offset=1)
        for i in range(3):
            event = self.client.send_event(Event(event_key=EventKey(name='name_{}'.format(i)),
                                                 message='message_{}'.format(i)))
        self.client.unregister_listener(l_id)
        self.assertEqual(2, processor.counter)

    def test_register_listener_with_event_key(self):
        class Counter(ListenerProcessor):
            def __init__(self):
                self.counter = 0

            def process(self, events: List[Event]):
                self.counter += len(events)
        processor = Counter()
        l_id = self.client.register_listener(listener_processor=processor,
                                             event_keys=[EventKey(name='name_2', namespace=None),
                                                         EventKey(name='name_3', namespace=None)])
        for i in range(5):
            event = self.client.send_event(Event(event_key=EventKey(name='name_{}'.format(i)),
                                                 message='message_{}'.format(i)))
        self.client.unregister_listener(l_id)
        self.assertEqual(2, processor.counter)

    def test_timestamp_to_event_offset(self):
        t1 = datetime.now()
        for i in range(5):
            if i == 3:
                t2 = datetime.now()
            event = self.client.send_event(Event(event_key=EventKey(name='name_{}'.format(i)),
                                                 message='message_{}'.format(i)))
        time.sleep(1)
        t3 = datetime.now()
        offset = self.client.time_to_offset(t1)
        self.assertEqual(0, offset)
        offset = self.client.time_to_offset(t2)
        self.assertEqual(3, offset)
        offset = self.client.time_to_offset(t3)
        self.assertEqual(5, offset)


if __name__ == '__main__':
    unittest.main()
