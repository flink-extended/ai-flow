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
import inspect
import os
import unittest

from ai_flow.common.module_load import import_string, load_module


class TestModuleLoad(unittest.TestCase):
    def test_import_string(self):
        a = import_string("unittest.TestCase")()
        self.assertTrue(isinstance(a, unittest.TestCase))

        with self.assertRaises(ImportError):
            import_string("invalid")

        with self.assertRaises(ImportError):
            import_string("test_util.ClassB")

    def test_load_module(self):
        full_path = os.path.join(os.path.dirname(__file__), 'load_module_for_test.py')
        mod = load_module(full_path)
        self.assertTrue('LOAD_OBJ' in mod.__dict__)
        self.assertTrue('NeedLoadedClass' in mod.__dict__)
