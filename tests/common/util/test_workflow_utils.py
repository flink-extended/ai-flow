#
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
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_flow.common.configuration import config_constants
from ai_flow.common.util import workflow_utils
from ai_flow.common.util.file_util.zip_file_util import make_dir_zipfile

BLOB_DIR = '/tmp/blob_for_test_workflow_utils'
BLOB_MANAGER_DEFAULT_VALUE = {
    'blob_manager_class': 'ai_flow.blob_manager.impl.local_blob_manager.LocalBlobManager',
    'blob_manager_config': {
        'root_directory': BLOB_DIR
    }
}


class TestWorkflowUtils(unittest.TestCase):

    def setUp(self) -> None:
        if not os.path.exists(BLOB_DIR):
            os.mkdir(BLOB_DIR)

    def tearDown(self) -> None:
        if os.path.exists(BLOB_DIR):
            shutil.rmtree(BLOB_DIR)

    def test_extract_workflows_from_file(self):
        workflows = workflow_utils.extract_workflows_from_file(
            os.path.join(os.path.dirname(__file__), 'for_test_workflow_utils/workflow.py')
        )
        self.assertEqual(2, len(workflows))
        self.assertEqual('workflow1', workflows[0].name)
        self.assertEqual('workflow2', workflows[1].name)

    def test_extract_workflows_from_zip(self):
        file_path = os.path.join(os.path.dirname(__file__), 'for_test_workflow_utils/workflow.py')
        with tempfile.TemporaryDirectory() as temp_dir:
            filename, _ = os.path.splitext(os.path.split(file_path)[-1])
            dest_dir = Path(temp_dir) / filename
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_dir)
            zip_file_name = '{}.zip'.format(filename)
            zip_file_path = Path(temp_dir) / zip_file_name
            make_dir_zipfile(dest_dir, zip_file_path)

            workflows = workflow_utils.extract_workflows_from_zip(zip_file_path, temp_dir)
            self.assertEqual(2, len(workflows))

    @mock.patch.object(config_constants, 'BLOB_MANAGER', BLOB_MANAGER_DEFAULT_VALUE)
    def test_upload_workflow_snapshot(self):
        file_path = os.path.join(os.path.dirname(__file__), 'for_test_workflow_utils/workflow.py')
        artifact = os.path.join(os.path.dirname(__file__), 'for_test_workflow_utils/artifact')
        workflow_utils.upload_workflow_snapshot(file_path=file_path,
                                                artifacts=[artifact, ])
        self.assertTrue(os.path.exists(os.path.join(BLOB_DIR, 'workflow.zip')))


