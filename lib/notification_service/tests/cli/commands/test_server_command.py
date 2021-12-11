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

import notification_service.settings
from notification_service.cli import cli_parser
from notification_service.cli.commands import server_command

logger = logging.getLogger(__name__)


class TestCliServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = cli_parser.get_parser()

    def test_cli_server_start(self):
        notification_home = os.path.join(os.path.dirname(__file__), "..", "..")
        notification_service.settings.NOTIFICATION_HOME = notification_home
        pid_file = os.path.join(notification_home, "notification_server.pid")

        with mock.patch.object(server_command, "NotificationServerRunner") as NotificationServerRunnerClass:
            mock_server_runner = mock.MagicMock()
            NotificationServerRunnerClass.side_effect = [mock_server_runner]

            with self.assertLogs("notification_service.cli.commands.server_command", "INFO") as log:
                server_command.server_start(self.parser.parse_args(['server', 'start']))
                log_output = "\n".join(log.output)

            NotificationServerRunnerClass.assert_called_once_with(
                os.path.join(notification_home, "notification_server.yaml"))
            self.assertIn("Starting notification server at pid", log_output)

            mock_server_runner.start.assert_called_once_with(True)
            self.assertFalse(os.path.exists(pid_file))

    def test_cli_server_start_daemon(self):
        notification_home = os.path.join(os.path.dirname(__file__), "..", "..")
        notification_service.settings.NOTIFICATION_HOME = notification_home
        with mock.patch.object(server_command, "_get_daemon_context") as get_daemon_context, \
                mock.patch.object(server_command, "NotificationServerRunner") as NotificationServerRunnerClass:
            get_daemon_context.return_value = mock.MagicMock()

            mock_server_runner = mock.MagicMock()
            NotificationServerRunnerClass.side_effect = [mock_server_runner]

            with self.assertLogs("notification_service.cli.commands.server_command", "INFO") as log:
                server_command.server_start(self.parser.parse_args(['server', 'start', '-d']))

            get_daemon_context.assert_called_once_with(mock.ANY, os.path.join(notification_home,
                                                                              "notification_server.pid"))
            log_output = "\n".join(log.output)
            self.assertIn("Starting Notification Server in daemon mode", log_output)
            self.assertIn("Notification server log:", log_output)
            self.assertIn("Notification server pid file:", log_output)
            mock_server_runner.start.assert_called_once_with(True)

    def test_cli_server_start_twice(self):
        notification_home = os.path.join(os.path.dirname(__file__), "..", "..")
        notification_service.settings.NOTIFICATION_HOME = notification_home
        pid_file_path = os.path.join(notification_home,
                                     notification_service.settings.NOTIFICATION_PID_FILENAME)
        with self.assertLogs("notification_service", "INFO") as log, TmpPidFile(pid_file_path), \
                mock.patch.object(server_command, "_get_daemon_context") as get_daemon_context, \
                mock.patch.object(server_command, "NotificationServerRunner") as NotificationServerRunnerClass:
            get_daemon_context.return_value = mock.MagicMock()
            mock_server_runner = mock.MagicMock()
            NotificationServerRunnerClass.side_effect = [mock_server_runner]

            with mock.patch.object(server_command, "check_pid_exist") as mock_check_pid_exist:
                mock_check_pid_exist.return_value = False
                server_command.server_start(self.parser.parse_args(['server', 'start']))
            self.assertIn('This means a staled PID file', str(log.output))

        with self.assertLogs("notification_service", "INFO") as log, TmpPidFile(pid_file_path), \
                mock.patch.object(server_command, "_get_daemon_context") as get_daemon_context, \
                mock.patch.object(server_command, "NotificationServerRunner") as NotificationServerRunnerClass:
            get_daemon_context.return_value = mock.MagicMock()
            mock_server_runner = mock.MagicMock()
            NotificationServerRunnerClass.side_effect = [mock_server_runner]
            with mock.patch.object(server_command, "check_pid_exist") as mock_check_pid_exist2:
                mock_check_pid_exist2.return_value = True
                server_command.server_start(self.parser.parse_args(['server', 'start']))
            self.assertIn('Notification Server is running', str(log.output))

    def test_cli_server_stop_without_pid_file(self):
        notification_home = os.path.join(os.path.dirname(__file__), "..", "..")
        notification_service.settings.NOTIFICATION_HOME = notification_home

        with self.assertLogs("notification_service.cli.commands.server_command", "INFO") as log:
            server_command.server_stop(self.parser.parse_args(['server', 'stop']))
            log_output = "\n".join(log.output)
            self.assertIn("PID file of Notification server does not exist at", log_output)

    def test_cli_server_stop_with_staled_pid_file(self):
        notification_home = os.path.join(os.path.dirname(__file__), "..", "..")
        notification_service.settings.NOTIFICATION_HOME = notification_home
        pid_file = os.path.join(notification_home, notification_service.settings.NOTIFICATION_PID_FILENAME)

        with self.assertLogs("notification_service", "INFO") as log, TmpPidFile(pid_file), \
                mock.patch.object(server_command, "check_pid_exist") as mock_check_pid_exist:
            mock_check_pid_exist.return_value = False
            server_command.server_stop(self.parser.parse_args(['server', 'stop']))
            log_output = "\n".join(log.output)
            self.assertIn("This means a staled PID file.", log_output)
            self.assertFalse(os.path.exists(pid_file))

    def test_cli_server_stop(self):
        notification_home = os.path.join(os.path.dirname(__file__), "..", "..")
        notification_service.settings.NOTIFICATION_HOME = notification_home
        pid_file = os.path.join(notification_home, notification_service.settings.NOTIFICATION_PID_FILENAME)
        with TmpPidFile(pid_file), \
                mock.patch.object(server_command, "stop_process") as mock_stop_process, \
                mock.patch.object(server_command, "check_pid_exist") as mock_check_pid_exist:
            mock_check_pid_exist.return_value = True
            server_command.server_stop(self.parser.parse_args(['server', 'stop']))
            mock_stop_process.assert_called_with(15213, "Notification server")


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
