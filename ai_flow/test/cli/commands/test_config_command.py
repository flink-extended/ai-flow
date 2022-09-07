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
import io
import logging
import os
import unittest
from contextlib import redirect_stdout

from ai_flow.cli import cli_parser
from ai_flow.cli.commands.config_command import config_init, config_get_value, config_list
from ai_flow.settings import AIFLOW_HOME

logger = logging.getLogger(__name__)


class TestCliConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = cli_parser.get_parser()

    def setUp(self) -> None:
        self.config_file = AIFLOW_HOME + '/aiflow_server.yaml'
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_cli_config_get_value(self):
        config_init(self.parser.parse_args(['config', 'init']))
        with redirect_stdout(io.StringIO()) as stdout:
            config_get_value(self.parser.parse_args(['config', 'get-value', 'server_port']))
            self.assertEquals('50051', str.splitlines(stdout.getvalue())[0])
        with self.assertRaises(SystemExit):
            config_get_value(self.parser.parse_args(['config', 'get-value', 'server_ip']))

    def test_cli_config_init(self):
        with self.assertLogs('ai_flow.cli.commands.config_command', 'INFO') as log:
            config_init(self.parser.parse_args(['config', 'init']))
            log_output = '\n'.join(log.output)
            self.assertIn('AIFlow server config generated at {}.'.format(self.config_file), log_output)

            config_init(self.parser.parse_args(['config', 'init']))
            log_output = "\n".join(log.output)
            self.assertIn('AIFlow server config has already initialized at {}.'.format(self.config_file),
                          log_output)

    def test_cli_config_list(self):
        config_init(self.parser.parse_args(['config', 'init']))
        with redirect_stdout(io.StringIO()) as stdout:
            config_list(self.parser.parse_args(['config', 'list']))
            self.assertIn('# port of AIFlow server\nserver_port: 50051\n', stdout.getvalue())
