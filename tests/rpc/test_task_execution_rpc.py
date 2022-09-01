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
import json
from unittest import mock
import cloudpickle

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.db_util.session import create_session
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.model.internal.events import SchedulingEventType
from ai_flow.operators.bash import BashOperator
from ai_flow.model.status import WorkflowStatus
from ai_flow.model.workflow import Workflow
from ai_flow.rpc.client.aiflow_client import get_scheduler_client
from ai_flow.rpc.server.server import AIFlowServer
from tests.test_utils.mock_utils import MockNotificationClient, MockTimer
from tests.test_utils.unittest_base import BaseUnitTest


class TestTaskExecutionRpc(BaseUnitTest):
    def setUp(self) -> None:
        super().setUp()
        with mock.patch("ai_flow.task_executor.common.task_executor_base.HeartbeatManager"):
            with mock.patch('ai_flow.rpc.service.scheduler_service.get_notification_client', MockNotificationClient):
                with mock.patch('ai_flow.task_executor.task_executor.TaskExecutorFactory.get_task_executor'):
                    self.server = AIFlowServer()
                    self.server.run(is_block=False)
        self.client = get_scheduler_client()
        self.notification_client = self.server.scheduler_service.notification_client
        self.workflow_meta = self.prepare_workflow()
        self.workflow_execution = self.prepare_workflow_execution(1, 1)

    def tearDown(self) -> None:
        self.server.stop()
        super().tearDown()

    def prepare_workflow(self):
        with Workflow(name='workflow1') as workflow:
            BashOperator(name='bash', bash_command='echo 1')
        workflow_meta = self.client.add_workflow(workflow.name, 'default', 'mock_content', cloudpickle.dumps(workflow))
        self.client.add_workflow_snapshot(workflow_meta.id, 'uri', cloudpickle.dumps(workflow), 'md5')
        return workflow_meta

    @staticmethod
    def prepare_workflow_execution(workflow_id, snapshot_id):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            return metadata_manager.add_workflow_execution(workflow_id=workflow_id,
                                                           run_type='manual',
                                                           snapshot_id=snapshot_id)

    @staticmethod
    def prepare_task_execution(workflow_execution_id):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            metadata_manager.add_task_execution(workflow_execution_id, 'task1')
            metadata_manager.add_task_execution(workflow_execution_id, 'task1')
            metadata_manager.add_task_execution(workflow_execution_id, 'task2')

    def test_start_task_execution(self):
        key = self.client.start_task_execution(
            workflow_execution_id=self.workflow_execution.id, task_name='bash')
        self.assertEqual(f'{self.workflow_execution.id}_bash_1', key)

    def test_stop_task_execution(self):
        self.prepare_task_execution(self.workflow_execution.id)
        self.client.stop_task_execution(1, 'task1')
        self.assertEqual(SchedulingEventType.STOP_TASK_EXECUTION,
                         self.notification_client.list_events()[0].value)
        self.assertEqual(json.dumps({"workflow_execution_id": 1, "task_execution_id": 2}),
                         self.notification_client.list_events()[0].context)

    def test_get_task_execution(self):
        self.prepare_task_execution(self.workflow_execution.id)
        execution = self.client.get_task_execution(1)
        self.assertEqual(1, execution.id)
        self.assertEqual(1, execution.workflow_execution_id)
        self.assertEqual('task1', execution.task_name)
        self.assertEqual(1, execution.sequence_number)
        self.assertEqual(WorkflowStatus.INIT.value, execution.status)

    def test_list_workflow_executions(self):
        self.prepare_task_execution(self.workflow_execution.id)
        executions = self.client.list_task_executions(self.workflow_execution.id)
        self.assertEqual(3, len(executions))
        executions = self.client.list_task_executions(
            workflow_execution_id=self.workflow_execution.id, page_size=3, offset=1)
        self.assertEqual(2, len(executions))

    def test_list_non_exists_workflow_executions(self):
        with self.assertRaisesRegex(AIFlowException, r"Workflow execution with id: 101 not exists"):
            self.client.list_task_executions(101)

    def test_stop_non_exists_workflow_executions(self):
        with self.assertRaisesRegex(AIFlowException, r'Task execution 101.invalid not exists'):
            self.client.stop_task_execution(101, 'invalid')
