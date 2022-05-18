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
import os
import tempfile
import unittest
from unittest import mock

from ai_flow.common.configuration import config_constants
from ai_flow.sdk import operation


class TestOperation(unittest.TestCase):

    def test__extract_workflows(self):
        workflows = operation._extract_workflows('./__init__.py')
        self.assertEqual(0, len(workflows))

        workflows = operation._extract_workflows('./workflow_for_test.py')
        self.assertEqual(3, len(workflows))
        self.assertEqual('workflow_1', workflows[0].name)
        self.assertEqual('workflow_2', workflows[1].name)
        self.assertEqual('workflow_3', workflows[2].name)

    def test__extract_workflows_failed(self):
        content = "workflow = Workflow(name='workflow')"
        with tempfile.NamedTemporaryFile() as f:
            f.write(content.encode('utf8'))
            f.flush()
            with self.assertRaises(NameError):
                operation._extract_workflows(f.name)

    def test__upload_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, 'workflow.py'), 'w') as f1:
                f1.write('A workflow')

            blob_root_dir = os.path.join(temp_dir, 'blob')
            blob_config = {
                'blob_manager_class': 'ai_flow.blob_manager.impl.local_blob_manager.LocalBlobManager',
                'blob_manager_config': {
                    'root_directory': blob_root_dir
                }
            }
            os.makedirs(blob_root_dir)
            with mock.patch.object(config_constants, "BLOB_MANAGER", blob_config):
                file_hash, uploaded_path = operation._upload_snapshot(f1.name)
                self.assertEqual(os.path.join(blob_root_dir, 'workflow.zip'), uploaded_path)
