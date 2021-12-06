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
import signal
import time
import unittest
from unittest import mock

import ai_flow.settings
import daemon
from ai_flow.cli import cli_parser
from ai_flow.cli.commands import webserver_command

logger = logging.getLogger(__name__)


class TestCliServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = cli_parser.get_parser()

    def test_cli_webserver_start(self):
        aiflow_home = os.path.join(os.path.dirname(__file__), "..")
        ai_flow.settings.AIFLOW_HOME = aiflow_home
        with mock.patch.object(webserver_command, "start_web_server_by_config_file_path") as start_web_server:
            webserver_command.webserver_start(self.parser.parse_args(['webserver', 'start']))
            start_web_server.assert_called_once_with(
                os.path.join(aiflow_home, "aiflow_server.yaml"))

            self.assertFalse(os.path.exists(os.path.join(aiflow_home, ai_flow.settings.AIFLOW_PID_FILENAME)))

    def test_cli_webserver_start_daemon(self):
        aiflow_home = os.path.join(os.path.dirname(__file__), "..")
        ai_flow.settings.AIFLOW_HOME = aiflow_home
        with mock.patch.object(daemon, "DaemonContext") as DaemonContext, \
                mock.patch.object(webserver_command, "start_web_server_by_config_file_path") as start_web_server:
            DaemonContext.side_effect = mock.MagicMock()

            with self.assertLogs("ai_flow.cli.commands.webserver_command", "INFO") as log:
                webserver_command.webserver_start(self.parser.parse_args(['webserver', 'start', '-d']))

            DaemonContext.assert_called_once()
            log_output = "\n".join(log.output)
            self.assertIn("Starting AIFlow Webserver in daemon mode", log_output)
            self.assertIn("AIFlow Webserver log:", log_output)
            self.assertIn("AIFlow Webserver pid file:", log_output)
            start_web_server.assert_called_once_with(os.path.join(aiflow_home, "aiflow_server.yaml"))

    def test_cli_webserver_stop_without_pid_file(self):
        aiflow_home = os.path.join(os.path.dirname(__file__), "..")
        ai_flow.settings.AIFLOW_HOME = aiflow_home

        with self.assertLogs("ai_flow.cli.commands.webserver_command", "INFO") as log:
            webserver_command.webserver_stop(self.parser.parse_args(['webserver', 'stop']))
            log_output = "\n".join(log.output)
            self.assertIn("PID file of AIFlow Webserver does not exist at", log_output)

    def test_cli_webserver_stop_SIGTERM_fail(self):
        aiflow_home = os.path.join(os.path.dirname(__file__), "..")
        ai_flow.settings.AIFLOW_HOME = aiflow_home
        pid_file = os.path.join(aiflow_home, ai_flow.settings.AIFLOW_WEBSERVER_PID_FILENAME)
        with mock.patch.object(os, "kill") as mock_kill, TmpPidFile(pid_file), \
                mock.patch.object(webserver_command, "check_pid_exist") as mock_pid_check:
            mock_kill.side_effect = [RuntimeError("Boom"), None]
            mock_pid_check.side_effect = [False]
            with self.assertLogs("ai_flow.cli.commands.webserver_command", "INFO") as log:
                webserver_command.webserver_stop(self.parser.parse_args(['webserver', 'stop']))
                log_output = "\n".join(log.output)
                self.assertIn("Failed to stop AIFlow Webserver", log_output)
                self.assertIn("stopped", log_output)

    def test_cli_webserver_stop_SIGTERM_SIGKILL_fail(self):
        aiflow_home = os.path.join(os.path.dirname(__file__), "..")
        ai_flow.settings.AIFLOW_HOME = aiflow_home
        pid_file = os.path.join(aiflow_home, ai_flow.settings.AIFLOW_WEBSERVER_PID_FILENAME)
        with mock.patch.object(os, "kill") as mock_kill, TmpPidFile(pid_file):
            mock_kill.side_effect = [RuntimeError("Boom"), RuntimeError("Boom")]
            with self.assertLogs("ai_flow.cli.commands.webserver_command", "INFO") as log:
                with self.assertRaises(RuntimeError):
                    webserver_command.webserver_stop(self.parser.parse_args(['webserver', 'stop']))
                log_output = "\n".join(log.output)
                self.assertIn("Failed to stop AIFlow Webserver", log_output)

    def test_cli_webserver_stop_wait_process_exit_timeout(self):
        aiflow_home = os.path.join(os.path.dirname(__file__), "..")
        ai_flow.settings.AIFLOW_HOME = aiflow_home
        pid_file = os.path.join(aiflow_home, ai_flow.settings.AIFLOW_WEBSERVER_PID_FILENAME)

        with mock.patch.object(os, "kill") as mock_kill, \
                TmpPidFile(pid_file), mock.patch.object(time, 'monotonic') as mock_monotonic:
            mock_kill.return_value = True
            mock_monotonic.side_effect = [0.0, 30.0, 70.0]
            with self.assertRaises(RuntimeError):
                webserver_command.webserver_stop(self.parser.parse_args(['server', 'stop']))
            self.assertEqual(3, mock_monotonic.call_count)

    def test_cli_webserver_stop(self):
        aiflow_home = os.path.join(os.path.dirname(__file__), "..")
        ai_flow.settings.AIFLOW_HOME = aiflow_home
        pid_file = os.path.join(aiflow_home, ai_flow.settings.AIFLOW_WEBSERVER_PID_FILENAME)
        with mock.patch.object(os, "kill") as mock_kill, TmpPidFile(pid_file), \
                mock.patch.object(webserver_command, "check_pid_exist") as mock_pid_check:
            mock_pid_check.side_effect = [True, False]
            webserver_command.webserver_stop(self.parser.parse_args(['webserver', 'stop']))
            mock_kill.assert_called_once_with(15213, signal.SIGTERM)
            self.assertEqual(2, mock_pid_check.call_count)


class TmpPidFile:
    def __init__(self, pid_file_path, pid: int = 15213):
        self.pid_file_path = pid_file_path
        self.pid = pid

    def __enter__(self):
        with open(self.pid_file_path, 'w') as f:
            f.write(str(self.pid))

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.pid_file_path):
            os.remove(self.pid_file_path)
