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

import sqlalchemy

from ai_flow.store.db.base_model import base
from ai_flow.util import sqlalchemy_db

SQLITE_FILE = 'ai_flow.db'
TEST_URL = 'sqlite:///ai_flow.db'


def create_engine(url):
    return sqlalchemy.create_engine(url)


def get_tables(url):
    return sqlalchemy.inspect(create_engine(url)).get_table_names()


def all_ai_flow_tables_exist(url):
    tables = set(get_tables(url))
    for key in base.metadata.tables.keys():
        if key not in tables:
            return False
    return True


def none_ai_flow_tables_exist(url):
    tables = set(get_tables(url))
    for key in base.metadata.tables.keys():
        if key in tables:
            return False
    return True


class TestSqlalchemyDB(unittest.TestCase):
    def setUp(self) -> None:
        sqlalchemy_db.clear_db(TEST_URL, base.metadata)

    def tearDown(self) -> None:
        if os.path.exists(SQLITE_FILE):
            os.remove(SQLITE_FILE)

    def test_upgrade(self):
        self.assertTrue(none_ai_flow_tables_exist(TEST_URL))
        sqlalchemy_db.upgrade(TEST_URL)
        self.assertTrue(all_ai_flow_tables_exist(TEST_URL))

    def test_upgrade_with_version(self):
        self.assertTrue(none_ai_flow_tables_exist(TEST_URL))
        sqlalchemy_db.upgrade(TEST_URL, 'de1c96ef582a')
        self.assertFalse(all_ai_flow_tables_exist(TEST_URL))
        self.assertTrue(len(get_tables(TEST_URL)) > 0)
        sqlalchemy_db.upgrade(TEST_URL)
        self.assertTrue(all_ai_flow_tables_exist(TEST_URL))

    def test_downgrade(self):
        self.assertTrue(none_ai_flow_tables_exist(TEST_URL))
        sqlalchemy_db.upgrade(TEST_URL)
        self.assertTrue(all_ai_flow_tables_exist(TEST_URL))
        sqlalchemy_db.downgrade(TEST_URL, 'de1c96ef582a')
        self.assertFalse(all_ai_flow_tables_exist(TEST_URL))


if __name__ == '__main__':
    unittest.main()
