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
import logging
import os
import unittest
from unittest import mock

import ai_flow.settings
from ai_flow.cli import cli_parser
from ai_flow.cli.commands import server_command

logger = logging.getLogger(__name__)


class TestCliServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = cli_parser.get_parser()

    def test_cli_server_start(self):
        aiflow_home = os.path.join(os.path.dirname(__file__), "..")
        ai_flow.settings.AIFLOW_HOME = aiflow_home
        with mock.patch.object(server_command, "AIFlowServerRunner") as AIFlowServerRunnerClass:
            mock_server_runner = mock.MagicMock()
            AIFlowServerRunnerClass.side_effect = [mock_server_runner]

            server_command.server_start(self.parser.parse_args(['server', 'start']))
            AIFlowServerRunnerClass.assert_called_once_with(
                os.path.join(aiflow_home, "aiflow_server.yaml"))

            mock_server_runner.start.assert_called_once_with(True)

    def test_cli_server_start_daemon(self):
        aiflow_home = os.path.join(os.path.dirname(__file__), "..")
        ai_flow.settings.AIFLOW_HOME = aiflow_home
        with mock.patch.object(server_command, "_get_daemon_context") as get_daemon_context, \
                mock.patch.object(server_command, "AIFlowServerRunner") as AIFlowServerRunnerClass:
            get_daemon_context.return_value = mock.MagicMock()

            mock_server_runner = mock.MagicMock()
            AIFlowServerRunnerClass.side_effect = [mock_server_runner]

            with self.assertLogs("ai_flow.cli.commands.server_command", "INFO") as log:
                server_command.server_start(self.parser.parse_args(['server', 'start', '-d']))

            get_daemon_context.assert_called_once_with(mock.ANY, os.path.join(aiflow_home,
                                                                              "aiflow_server.pid"))
            log_output = "\n".join(log.output)
            self.assertIn("Starting AIFlow Server in daemon mode", log_output)
            self.assertIn("AIFlow server log:", log_output)
            self.assertIn("AIFlow server pid file:", log_output)
            mock_server_runner.start.assert_called_once_with(True)
