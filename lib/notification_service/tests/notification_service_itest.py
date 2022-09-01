#
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
from typing import List
import unittest

import pytest
from notification_service.client.notification_client import ListenerProcessor
from notification_service.model.event import Event, EventKey
from notification_service.client.embedded_notification_client import EmbeddedNotificationClient
from notification_service.rpc.service import HighAvailableNotificationService, NotificationService
from notification_service.server.ha_manager import SimpleNotificationServerHaManager
from notification_service.server.server import NotificationServer
from notification_service.storage.alchemy import ClientModel
from notification_service.storage.alchemy.db_high_availability_storage import DbHighAvailabilityStorage
from notification_service.storage.in_memory.memory_event_storage import MemoryEventStorage
from notification_service.storage.alchemy.db_event_storage import DbEventStorage
from notification_service.storage.mongo.mongo_event_storage import MongoEventStorage
from notification_service.util import db
from notification_service.util.db import SQL_ALCHEMY_DB_FILE


class TestListenerProcessor(ListenerProcessor):
    def __init__(self, event_list) -> None:
        super().__init__()
        self.event_list = event_list

    def process(self, events: List[Event]):
        self.event_list.extend(events)


def start_ha_master(host, port):
    server_uri = host + ":" + str(port)
    storage = DbEventStorage()
    ha_manager = SimpleNotificationServerHaManager()
    ha_storage = DbHighAvailabilityStorage()
    service = HighAvailableNotificationService(
        storage,
        ha_manager,
        server_uri,
        ha_storage)
    master = NotificationServer(service, port=port)
    master.run()
    return master


properties = {'enable.idempotence': 'True'}


class NotificationTestBase(object):

    def _prepare_events(self):
        self.client.namespace = "namespace_a"
        self.client.sender = 'sender'
        self.client.send_event(
            Event(
                event_key=EventKey(event_name="key"),
                message="value1"
            )
        )
        self.client.namespace = "namespace_b"
        self.client.send_event(
            Event(
                event_key=EventKey(event_name="key", event_type="type_a"),
                message="value2"
            )
        )
        self.client.send_event(
            Event(
                event_key=EventKey(event_name="key"),
                message="value3"
            )
        )
        self.client.send_event(
            Event(
                event_key=EventKey(event_name="key2"),
                message="value3"
            )
        )

    def test_send_event(self):
        event = self.client.send_event(
            Event(
                event_key=EventKey(event_name="key"),
                message="value1"
            )
        )
        self.assertTrue(event.offset >= 1)

    def test_list_events(self):
        self._prepare_events()

        events = self.client.list_events(event_name="key", namespace="namespace_a")
        self.assertEqual(1, len(events))
        events = self.client.list_events("key", namespace="namespace_b")
        self.assertEqual(2, len(events))
        events = self.client.list_events("key", event_type="type_a")
        self.assertEqual(1, len(events))
        events = self.client.list_events("key", sender='sender')
        self.assertEqual(3, len(events))
        events = self.client.list_events("key", sender='invalid')
        self.assertEqual(0, len(events))
        events = self.client.list_events("key", begin_offset=1, end_offset=2)
        self.assertEqual(2, len(events))
        self.assertEqual('value2', events[0].message)
        self.assertEqual('value3', events[1].message)



    def test_count_events(self):
        self._prepare_events()

        count = self.client.count_events("key", namespace="namespace_a")
        self.assertEqual(1, count[0])
        count = self.client.count_events("key", namespace="namespace_b")
        self.assertEqual(2, count[0])
        count = self.client.count_events("key", event_type="type_a")
        self.assertEqual(1, count[0])
        count = self.client.count_events("key", sender="sender")
        self.assertEqual(3, count[0])
        self.assertEqual(3, count[1][0].event_count)
        count = self.client.count_events("key", sender="invalid")
        self.assertEqual(0, count[0])
        self.assertEqual([], count[1])

    def test_listen_events(self):
        event_list = []
        self.client.namespace = "a"
        self.client.sender = "s"
        try:
            event1 = self.client.send_event(Event(EventKey("key"), message="value1"))
            handle = self.client.register_listener(
                listener_processor=TestListenerProcessor(event_list),
                event_keys=[EventKey("key", None)],
                offset=event1.offset
            )
            self.client.send_event(Event(EventKey("key"), message="value2"))

            self.client.namespace = None
            self.client.send_event(Event(EventKey("key"), message="value3"))
        finally:
            self.client.unregister_listener(handle)

        self.client.namespace = "a"
        events = self.client.list_events("key", begin_offset=event1.offset)
        self.assertEqual(2, len(events))
        self.assertEqual(2, len(event_list))

    def test_listen_events_by_event_type(self):
        event_list = []
        try:
            handle = self.client.register_listener(
                listener_processor=TestListenerProcessor(event_list),
                event_keys=[EventKey(event_name="key", event_type="e")]
            )
            self.client.send_event(Event(EventKey(event_name="key", event_type="e"), "value2"))
            self.client.send_event(Event(EventKey(event_name="key", event_type="f"), "value2"))
        finally:
            self.client.unregister_listener(handle)
        self.assertEqual(1, len(event_list))
        self.assertEqual("e", event_list[0].event_key.event_type)

    def test_list_all_events(self):
        self.client.send_event(Event(EventKey("key"), "value1"))
        time.sleep(1.0)
        event2 = self.client.send_event(Event(EventKey("key"), "value2"))
        start_time = event2.create_time
        self.client.send_event(Event(EventKey("key"), "value3"))
        events = self.client.list_all_events(start_time)
        self.assertEqual(2, len(events))

    def test_list_all_events_with_id_range(self):
        event1 = self.client.send_event(Event(EventKey("key"), "value1"))
        self.client.send_event(Event(EventKey("key"), "value2"))
        event3 = self.client.send_event(Event(EventKey("key"), "value3"))
        events = self.client.list_all_events(start_offset=event1.offset, end_offset=event3.offset)
        self.assertEqual(2, len(events))

    def test_listen_all_events(self):
        event_list = []
        handle = None
        try:
            handle = self.client.register_listener(listener_processor=TestListenerProcessor(event_list))
            self.client.send_event(Event(EventKey("key"), "value1"))
            self.client.send_event(Event(EventKey("key"), "value2"))
            self.client.send_event(Event(EventKey("key"), "value3"))
        finally:
            if handle is not None:
                self.client.unregister_listener(handle)
        self.assertEqual(3, len(event_list))

    def test_listen_all_events_from_id(self):
        event_list = []
        handle = None
        try:
            event1 = self.client.send_event(Event(EventKey("key"), message="value1"))
            handle = self.client.register_listener(
                listener_processor=TestListenerProcessor(event_list), offset=event1.offset
            )
            self.client.send_event(Event(EventKey("key"), "value2"))
            self.client.send_event(Event(EventKey("key"), "value3"))
        finally:
            self.client.unregister_listener(handle)
        self.assertEqual(2, len(event_list))

    def test_register_client(self):
        self.assertIsNotNone(self.client.client_id)
        tmp_client = EmbeddedNotificationClient(server_uri="localhost:50051",
                                                namespace=None,
                                                sender=None)
        self.assertEqual(1, tmp_client.client_id - self.client.client_id)

    def test_is_client_exists(self):
        client_id = self.client.client_id
        self.assertIsNotNone(client_id)
        self.assertEqual(True, self.storage.is_client_exists(client_id))

    def test_delete_client(self):
        client_id = self.client.client_id
        self.assertIsNotNone(client_id)
        self.client.close()
        self.assertEqual(False, self.storage.is_client_exists(client_id))

    def test_send_event_idempotence(self):
        event = Event(EventKey("key"), "value1")
        self.client.send_event(event)
        self.assertEqual(1, self.client.sequence_num_manager.get_sequence_number())
        self.assertEqual(1, len(self.client.list_events(event_name="key")))

        self.client.send_event(event)
        self.assertEqual(2, self.client.sequence_num_manager.get_sequence_number())
        self.assertEqual(2, len(self.client.list_events(event_name="key")))

        self.client.sequence_num_manager._seq_num = 1
        self.client.send_event(event)
        self.assertEqual(2, self.client.sequence_num_manager.get_sequence_number())
        self.assertEqual(2, len(self.client.list_events(event_name="key")))

    def test_client_recovery(self):
        event = Event(EventKey("key"), "value1")

        self.client.send_event(event)
        self.client.send_event(event)
        self.assertEqual(2, self.client.sequence_num_manager.get_sequence_number())
        self.assertEqual(2, len(self.client.list_events(event_name="key")))

        client2 = EmbeddedNotificationClient(server_uri="localhost:50051",
                                             namespace=None,
                                             sender=None,
                                             client_id=self.client.client_id,
                                             initial_seq_num=1)
        client2.send_event(event)
        self.assertEqual(2, client2.sequence_num_manager.get_sequence_number())
        self.assertEqual(2, len(client2.list_events(event_name="key")))

        client2.send_event(event)
        self.assertEqual(3, client2.sequence_num_manager.get_sequence_number())
        self.assertEqual(3, len(client2.list_events(event_name="key")))


class DbStorageTest(unittest.TestCase, NotificationTestBase):

    @classmethod
    def set_up_class(cls):
        db.create_all_tables()
        cls.storage = DbEventStorage()
        cls.master = NotificationServer(NotificationService(cls.storage))
        cls.master.run()
        cls.wait_for_master_started("localhost:50051")

    @classmethod
    def setUpClass(cls):
        cls.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.master.stop()
        os.remove(SQL_ALCHEMY_DB_FILE)

    def setUp(self):
        db.prepare_db()
        self.storage.clean_up()
        self.client = EmbeddedNotificationClient(server_uri="localhost:50051",
                                                 namespace=None,
                                                 sender=None)

    def tearDown(self):
        db.clear_engine_and_session()

    def test_db_clean_up(self):
        try:
            db.clear_engine_and_session()
            global_db_uri = db.SQL_ALCHEMY_CONN
            db_file = 'test_ns.db'
            db_uri = 'sqlite:///{}'.format(db_file)
            store = DbEventStorage(db_uri)
            db.upgrade(db_uri, '87cb292bcc31')
            db.prepare_db()
            with db.create_session() as session:
                client = ClientModel()
                client.namespace = 'a'
                client.sender = 'a'
                client.create_time = 1
                session.add(client)
                session.commit()
                client_res = session.query(ClientModel).all()
                self.assertEqual(1, len(client_res))
            store.clean_up()
            client_res = session.query(ClientModel).all()
            self.assertEqual(0, len(client_res))
            self.assertTrue(db.tables_exists(db_uri))
        finally:
            db.SQL_ALCHEMY_CONN = global_db_uri
            db.clear_engine_and_session()
            if os.path.exists(db_file):
                os.remove(db_file)

    @classmethod
    def wait_for_master_started(cls, server_uri="localhost:50051"):
        last_exception = None
        for i in range(60):
            try:
                return EmbeddedNotificationClient(server_uri=server_uri,
                                                  namespace=None,
                                                  sender=None)
            except Exception as e:
                time.sleep(2)
                last_exception = e
        raise Exception("The server %s is unavailable." % server_uri) from last_exception


class MemoryStorageTest(unittest.TestCase, NotificationTestBase):

    @classmethod
    def set_up_class(cls):
        cls.storage = MemoryEventStorage()
        cls.master = NotificationServer(NotificationService(cls.storage))
        cls.master.run()

    @classmethod
    def setUpClass(cls):
        cls.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.master.stop()

    def setUp(self):
        self.storage.clean_up()
        self.client = EmbeddedNotificationClient(server_uri="localhost:50051",
                                                 namespace=None,
                                                 sender=None)

    def tearDown(self):
        pass


@unittest.skip("To run this test you need to setup a local mongodb")
@pytest.mark.release
class MongoNotificationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        kwargs = {
            "host": "127.0.0.1",
            "port": 27017,
            "db": "test"
        }
        cls.storage = MongoEventStorage(**kwargs)
        cls.master = NotificationServer(NotificationService(cls.storage))
        cls.master.run()
        cls.client = EmbeddedNotificationClient(server_uri="localhost:50051",
                                                namespace=None,
                                                sender=None)

    @classmethod
    def tearDownClass(cls):
        cls.master.stop()
        MongoNotificationTest.storage.clean_up()  # will clean up mongodb!!!

    def setUp(self):
        MongoNotificationTest.storage.clean_up()  # will clean up mongodb!!!


class HaDbStorageTest(unittest.TestCase, NotificationTestBase):
    """
    This test is used to ensure the high availability would not break the original functionality.
    """

    @classmethod
    def set_up_class(cls):
        db.create_all_tables()
        cls.storage = DbEventStorage()
        cls.master1 = start_ha_master("localhost", 50051)
        # The server startup is asynchronous, we need to wait for a while
        # to ensure it writes its metadata to the db.
        time.sleep(0.1)
        cls.master2 = start_ha_master("localhost", 50052)
        time.sleep(0.1)
        cls.master3 = start_ha_master("localhost", 50053)
        time.sleep(0.1)

    @classmethod
    def setUpClass(cls):
        cls.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.master1.stop()
        cls.master2.stop()
        cls.master3.stop()
        os.remove(SQL_ALCHEMY_DB_FILE)

    def setUp(self):
        db.prepare_db()
        self.storage.clean_up()
        self.client = EmbeddedNotificationClient(server_uri="localhost:50051,localhost:50052",
                                                 namespace=None,
                                                 sender=None)

    def tearDown(self):
        self.client.disable_high_availability()
        db.clear_engine_and_session()


class HaClientWithNonHaServerTest(unittest.TestCase, NotificationTestBase):

    @classmethod
    def wait_for_master_started(cls, server_uri):
        last_exception = None
        for i in range(100):
            try:
                return EmbeddedNotificationClient(
                    server_uri=server_uri,
                    namespace=None,
                    sender=None)
            except Exception as e:
                time.sleep(10)
                last_exception = e
        raise Exception("The server %s is unavailable." % server_uri) from last_exception

    @classmethod
    def setUpClass(cls):
        db.create_all_tables()
        cls.storage = DbEventStorage()
        cls.master = NotificationServer(NotificationService(cls.storage))
        cls.master.run()

    @classmethod
    def tearDownClass(cls):
        cls.master.stop()
        os.remove(SQL_ALCHEMY_DB_FILE)

    def setUp(self):
        db.prepare_db()
        self.storage.clean_up()
        self.client = self.wait_for_master_started(server_uri="localhost:50051,localhost:50052")

    def tearDown(self):
        db.clear_engine_and_session()
