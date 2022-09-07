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
import unittest

import ai_flow.settings
from ai_flow.settings import get_configuration, get_aiflow_home, get_configuration_file_path


class TestSettings(unittest.TestCase):

    def setUp(self) -> None:
        self.prev_AIFLOW_HOME = ai_flow.settings.AIFLOW_HOME

    def tearDown(self) -> None:
        ai_flow.settings.AIFLOW_HOME = self.prev_AIFLOW_HOME

    def test_get_configuration(self):
        ai_flow.settings.AIFLOW_HOME = os.path.dirname(__file__)
        config = get_configuration()
        self.assertEqual('sqlite:///aiflow.db', config.get_db_uri())
        self.assertEqual(50051, config.get_server_port())
        self.assertEqual('localhost:50052', config.get_notification_server_uri())

    def test_get_configuration_file_path(self):
        aiflow_home = os.path.dirname(__file__)
        ai_flow.settings.AIFLOW_HOME = aiflow_home
        self.assertEqual(os.path.join(aiflow_home, "aiflow_server.yaml"), get_configuration_file_path())

    def test_get_non_exist_configuration_file_path(self):
        ai_flow.settings.AIFLOW_HOME = '/non-exist-home'
        with self.assertRaises(FileNotFoundError):
            get_configuration_file_path()

    def test_get_aiflow_home(self):
        prev_home = os.environ['HOME']
        try:
            os.environ['HOME'] = '/home'
            self.assertEqual(os.path.join('/home', 'aiflow'), get_aiflow_home())
            os.environ['AIFLOW_HOME'] = '/aiflow_home'
            self.assertEqual('/aiflow_home', get_aiflow_home())

        finally:
            os.environ['HOME'] = prev_home
            if 'AIFLOW_HOME' in os.environ:
                del os.environ['AIFLOW_HOME']
