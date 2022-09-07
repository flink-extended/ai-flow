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
import signal
import time
import unittest
from unittest import mock

import notification_service
from notification_service.util.utils import import_string, check_pid_exist, stop_process


class TestUtil(unittest.TestCase):
    def test_import_string(self):
        a = import_string("unittest.TestCase")()
        self.assertTrue(isinstance(a, unittest.TestCase))

        with self.assertRaises(ImportError):
            import_string("invalid")

        with self.assertRaises(ImportError):
            import_string("test_util.ClassB")

    def test_check_pid_exist(self):
        with mock.patch("os.kill") as mock_kill:
            mock_kill.side_effect = [OSError, True]
            self.assertFalse(check_pid_exist(0))
            self.assertTrue(check_pid_exist(0))

    def test_stop_process_SIGTERM_fail(self):
        with mock.patch.object(os, "kill") as mock_kill, \
                mock.patch.object(notification_service.util.utils, "check_pid_exist") as mock_pid_check:
            mock_kill.side_effect = [RuntimeError("Boom"), None]
            with self.assertLogs("notification_service", "INFO") as log:
                mock_pid_check.side_effect = [True, False]
                stop_process(15213, "Dummy process")
                log_output = "\n".join(log.output)
                self.assertIn("Failed to stop Dummy process", log_output)
                self.assertIn("stopped", log_output)

    def test_stop_process_SIGTERM_SIGKILL_fail(self):
        with mock.patch.object(os, "kill") as mock_kill:
            mock_kill.side_effect = [RuntimeError("Boom"), RuntimeError("Boom")]
            with self.assertLogs("notification_service", "INFO") as log:
                with self.assertRaises(RuntimeError):
                    stop_process(15213, "Dummy process")
                log_output = "\n".join(log.output)
                self.assertIn("Failed to stop Dummy process", log_output)

    def test_stop_process_wait_process_exit_timeout(self):
        with mock.patch.object(os, "kill") as mock_kill, \
                mock.patch.object(time, 'monotonic') as mock_monotonic:
            mock_kill.return_value = True
            mock_monotonic.side_effect = [0.0, 30.0, 70.0]
            with self.assertLogs("notification_service", "INFO") as log:
                stop_process(15213, "Dummy process")
                log_output = "\n".join(log.output)
                self.assertIn("Failed to stop Dummy process", log_output)
            self.assertEqual(3, mock_monotonic.call_count)
            mock_kill.assert_any_call(15213, signal.SIGKILL)
