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
from queue import Full

from ai_flow.common.util.db_util import session
from ai_flow.common.util.db_util.db_migration import init_db
from ai_flow.common.util.db_util.session import create_session
from ai_flow.metadata.message import PersistentQueue


class TestObj:
    def __init__(self, data):
        self.data = data


class TestMessageQueue(unittest.TestCase):
    def setUp(self) -> None:
        self.file = 'test.db'
        self._delete_db_file()
        self.db_uri = 'sqlite:///{}'.format(self.file)
        init_db(self.db_uri)
        session.prepare_session(db_uri=self.db_uri)

    def _delete_db_file(self):
        if os.path.exists(self.file):
            os.remove(self.file)

    def tearDown(self) -> None:
        self._delete_db_file()
        session.clear_engine_and_session()

    def test_get_and_put(self):
        queue = PersistentQueue()

        queue.put(TestObj('aa'))
        queue.put(TestObj('bb'))
        self.assertEqual(2, queue.qsize())

        self.assertEqual('aa', queue.get().data)

        self.assertEqual(1, queue.qsize())

    def test__load_unprocessed_message(self):
        queue = PersistentQueue()
        queue.put(TestObj('aa'))
        queue.put(TestObj('bb'))
        queue2 = PersistentQueue()
        self.assertEqual(2, queue2.qsize())
        self.assertEqual('aa', queue2.get().data)
        self.assertEqual('bb', queue2.get().data)

        queue2.put(TestObj('cc'))
        queue2.put(TestObj('dd'))
        queue3 = PersistentQueue()
        self.assertEqual(4, queue3.qsize())
        self.assertEqual('aa', queue3.get().data)
        self.assertEqual('bb', queue3.get().data)
        self.assertEqual('cc', queue3.get().data)
        self.assertEqual('dd', queue3.get().data)

    def test_remove_expired(self):
        queue = PersistentQueue()
        queue.put(TestObj('aa'))
        queue.put(TestObj('bb'))

        queue.get()
        queue.remove_expired()

        self.assertEqual(1, queue.qsize())
        self.assertEqual('bb', queue.get().data)

    def test_queue_size(self):
        queue = PersistentQueue(maxsize=1)
        queue.put(TestObj('aa'))
        with self.assertRaises(Full):
            queue.put(TestObj('bb'), block=False)
