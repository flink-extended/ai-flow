#
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

from ai_flow.endpoint.server.server_config import AIFlowServerConfig, DBType


class TestConfiguration(unittest.TestCase):

    def test_dump_load_configuration(self):
        config = AIFlowServerConfig()
        config.set_db_uri(db_type=DBType.SQLITE, uri="sqlite:///sql.db")
        self.assertEqual('sql.db', config.get_sql_lite_db_file())

    def test_load_master_configuration(self):
        config = AIFlowServerConfig()
        config.load_from_file(os.path.dirname(__file__) + '/aiflow_server.yaml')
        self.assertEqual('sql_lite', config.get_db_type())
        self.assertEqual('/tmp/repo', config.get_scheduler_service_config()['repository'])
        self.assertEqual(True, config.start_scheduler_service())

    def test_get_wait_for_server_started_timeout(self):
        config = AIFlowServerConfig()
        config.load_from_file(os.path.dirname(__file__) + '/aiflow_server.yaml')
        self.assertEqual(5.0, config.get_wait_for_server_started_timeout())


if __name__ == '__main__':
    unittest.main()
