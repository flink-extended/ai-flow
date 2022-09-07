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
import unittest
import os
from ai_flow.common.util.db_util.db_migration import init_db, table_exists


class TestDBMigration(unittest.TestCase):

    def setUp(self) -> None:
        self.file = 'test.db'
        self.url = 'sqlite:///{}'.format(self.file)

    def tearDown(self) -> None:
        if os.path.exists(self.file):
            os.remove(self.file)

    def test_init_db(self):
        init_db(url=self.url)
        self.assertTrue(table_exists(url=self.url, table_name='namespace'))
        self.assertTrue(table_exists(url=self.url, table_name='workflow'))
        self.assertTrue(table_exists(url=self.url, table_name='workflow_snapshot'))
        self.assertTrue(table_exists(url=self.url, table_name='workflow_schedule'))
        self.assertTrue(table_exists(url=self.url, table_name='workflow_event_trigger'))
        self.assertTrue(table_exists(url=self.url, table_name='workflow_execution'))
        self.assertTrue(table_exists(url=self.url, table_name='task_execution'))
        self.assertTrue(table_exists(url=self.url, table_name='workflow_execution_state'))
        self.assertTrue(table_exists(url=self.url, table_name='workflow_state'))


if __name__ == '__main__':
    unittest.main()
