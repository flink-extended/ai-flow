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
from mock import patch

from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.task_execution import TaskExecution
from ai_flow.model.workflow import Workflow


class TestTaskExecution(unittest.TestCase):

    @patch('ai_flow.model.workflow_execution.get_workflow_snapshot')
    @patch('ai_flow.model.workflow_execution.get_workflow_name_by_execution_id')
    @patch('ai_flow.common.util.workflow_utils.extract_workflow')
    def test_get_task(self, mock_extract, mock_name, mock_snapshot):
        w1 = Workflow('workflow1')
        w2 = Workflow('workflow2')
        workflows = [w1, w2]
        mock_name.return_value = 'workflow1'
        mock_extract.return_value = workflows

        te = TaskExecution(workflow_execution_id=1001,
                           task_name='task',
                           sequence_number=2,
                           execution_type=ExecutionType.MANUAL)
        te.get_task()
        mock_name.assert_any_call(1001)
        mock_snapshot.assert_called_once_with(1001)
