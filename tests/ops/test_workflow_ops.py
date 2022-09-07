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
import os
import unittest
from unittest import mock

from ai_flow import ops


class TestWorkflowOps(unittest.TestCase):

    def setUp(self) -> None:
        self.workflow_file_path = os.path.join(os.path.dirname(__file__), 'workflow_for_unittest.py')

    @mock.patch('ai_flow.ops.workflow_ops.get_scheduler_client')
    def test_upload_new_workflows(self, mock_scheudler_client):
        mock_scheudler_client.return_value.get_workflow.return_value = None
        mock_workflow = mock.MagicMock()
        mock_scheudler_client.return_value.add_workflow.return_value = mock_workflow
        self.assertEqual([mock_workflow, mock_workflow], ops.upload_workflows(self.workflow_file_path))

    @mock.patch('ai_flow.ops.workflow_ops.get_scheduler_client')
    def test_upload_existed_workflows(self, mock_scheudler_client):
        mock_workflow = mock.MagicMock()
        mock_scheudler_client.return_value.get_workflow.return_value = mock_workflow
        new_workflow = mock.MagicMock()
        mock_scheudler_client.return_value.update_workflow.return_value = new_workflow
        self.assertEqual([new_workflow, new_workflow], ops.upload_workflows(self.workflow_file_path))
