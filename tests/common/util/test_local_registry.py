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

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.local_registry import LocalRegistry


class TestLocalRegistry(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self._registry = LocalRegistry("tmp_registry")

    def tearDown(self):
        del self._registry
        if os.path.exists("tmp_registry.bak"):
            os.remove("tmp_registry.bak")
        if os.path.exists("tmp_registry.dat"):
            os.remove("tmp_registry.dat")
        if os.path.exists("tmp_registry.dir"):
            os.remove("tmp_registry.dir")
        super().tearDown()

    def test_local_registry(self):
        self._registry.set('key1', 'value1')
        self.assertEqual(b'value1', self._registry.get('key1'))

        self._registry.set('key1', 'new_value1')
        self.assertEqual(b'new_value1', self._registry.get('key1'))

        self._registry.set('key2', 'value2')
        self.assertEqual(b'value2', self._registry.get('key2'))
        self.assertEqual(b'new_value1', self._registry.get('key1'))

        self._registry.remove('key1')
        self.assertEqual(b'value2', self._registry.get('key2'))
        self.assertIsNone(self._registry.get('key1'))

    def test_non_exist_dir(self):
        with self.assertRaisesRegex(AIFlowException, r'Parent directory of local registry not exists.'):
            LocalRegistry('/non-exists-dir/registry')

    def test_persistent(self):
        self._registry.set('key1', 'value1')
        new_registry = LocalRegistry("tmp_registry")
        self.assertEqual(b'value1', new_registry.get('key1'))


