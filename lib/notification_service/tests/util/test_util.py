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

import unittest
from unittest import mock

from notification_service.util.utils import import_string, check_pid_exist


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

