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
import unittest
import os
from sqlalchemy import create_engine
from notification_service.util import db

DB_FILE = 'ns.db'
DB_URL = 'sqlite:///{}'.format(DB_FILE)


class TestDB(unittest.TestCase):

    def setUp(self) -> None:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        db.SQL_ALCHEMY_CONN = DB_URL

    def tearDown(self) -> None:
        db.clear_engine_and_session()
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)

    def test_upgrade(self):
        db.upgrade(url=DB_URL)
        engine = create_engine(DB_URL)
        self.assertTrue('event_model' in engine.table_names())
        self.assertTrue('member_model' in engine.table_names())
        self.assertTrue('notification_client' in engine.table_names())

    def test_upgrade_with_version(self):
        db.upgrade(url=DB_URL, version='87cb292bcc31')
        engine = create_engine(DB_URL)
        self.assertTrue('event_model' in engine.table_names())
        self.assertTrue('notification_client' in engine.table_names())
        self.assertFalse('member_model' in engine.table_names())

    def test_downgrade(self):
        db.upgrade(url=DB_URL)
        engine = create_engine(DB_URL)
        self.assertTrue('member_model' in engine.table_names())
        db.downgrade(url=DB_URL, version='87cb292bcc31')
        self.assertFalse('member_model' in engine.table_names())

    def test_clear_db(self):
        db.upgrade(url=DB_URL)
        engine = create_engine(DB_URL)
        db.clear_db(url=DB_URL)
        self.assertFalse('event_model' in engine.table_names())
        self.assertFalse('notification_client' in engine.table_names())
        self.assertFalse('member_model' in engine.table_names())

    def test_reset_db(self):
        db.upgrade(url=DB_URL)
        engine = create_engine(DB_URL)
        db.reset_db(url=DB_URL)
        self.assertTrue('event_model' in engine.table_names())
        self.assertTrue('notification_client' in engine.table_names())
        self.assertTrue('member_model' in engine.table_names())

    def test_tables_exists(self):
        res = db.tables_exists(DB_URL)
        self.assertFalse(res)
        db.upgrade(DB_URL)
        res = db.tables_exists(DB_URL)
        self.assertTrue(res)


if __name__ == '__main__':
    unittest.main()
