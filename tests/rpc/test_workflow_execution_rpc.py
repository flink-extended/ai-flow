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


class TestWorkflowExecutionRpc(BaseUnitTest):
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
            metadata_manager.add_workflow_execution(workflow_id=workflow_id,
                                                    run_type='manual',
                                                    snapshot_id=snapshot_id)
            metadata_manager.add_workflow_execution(workflow_id=workflow_id,
                                                    run_type='manual',
                                                    snapshot_id=snapshot_id)
            metadata_manager.update_workflow_execution(1, WorkflowStatus.FAILED)

    def test_start_workflow_execution(self):
        id = self.client.start_workflow_execution(workflow_name=self.workflow_meta.name,
                                                  namespace=self.workflow_meta.namespace)
        self.assertEqual(1, id)

    def test_stop_workflow_execution(self):
        self.client.stop_workflow_execution(1)
        self.assertEqual(SchedulingEventType.STOP_WORKFLOW_EXECUTION,
                         self.notification_client.list_events()[0].value)
        self.assertEqual(json.dumps({'workflow_execution_id': 1}),
                         self.notification_client.list_events()[0].context)

    def test_stop_workflow_executions(self):
        self.prepare_workflow_execution(1, 1)
        self.client.stop_workflow_executions(namespace=self.workflow_meta.namespace,
                                             workflow_name=self.workflow_meta.name)
        self.assertEqual(SchedulingEventType.STOP_WORKFLOW_EXECUTION,
                         self.notification_client.list_events()[0].value)
        self.assertEqual(json.dumps({'workflow_execution_id': 2}),
                         self.notification_client.list_events()[0].context)

    def test_delete_workflow_execution(self):
        self.prepare_workflow_execution(1, 1)
        self.assertEqual(2, len(self.client.list_workflow_executions(
            workflow_name=self.workflow_meta.name, namespace=self.workflow_meta.namespace)))
        self.client.delete_workflow_execution(1)
        self.assertEqual(1, len(self.client.list_workflow_executions(
            workflow_name=self.workflow_meta.name, namespace=self.workflow_meta.namespace)))
        with self.assertRaisesRegex(AIFlowException, r'not finished, cannot be removed'):
            self.client.delete_workflow_execution(2)

    def test_get_workflow_execution(self):
        self.prepare_workflow_execution(1, 1)
        execution = self.client.get_workflow_execution(1)
        self.assertEqual(1, execution.id)
        self.assertEqual(1, execution.workflow_id)
        self.assertEqual(WorkflowStatus.FAILED.value, execution.status)
        self.assertEqual('manual', execution.run_type)
        self.assertEqual(1, execution.snapshot_id)
        self.assertEqual(-1, execution.event_offset)

    def test_list_workflow_executions(self):
        self.prepare_workflow_execution(1, 1)
        executions = self.client.list_workflow_executions(workflow_name=self.workflow_meta.name,
                                                          namespace=self.workflow_meta.namespace)
        self.assertEqual(2, len(executions))
        executions = self.client.list_workflow_executions(workflow_name=self.workflow_meta.name,
                                                          namespace=self.workflow_meta.namespace,
                                                          page_size=2,
                                                          offset=1)
        self.assertEqual(1, len(executions))

    def test_list_non_exists_workflow_executions(self):
        with self.assertRaisesRegex(AIFlowException, r'Workflow invalid.invalid not exists'):
            self.client.list_workflow_executions('invalid', 'invalid')

    def test_stop_non_exists_workflow_executions(self):
        with self.assertRaisesRegex(AIFlowException, r'Workflow invalid.invalid not exists'):
            self.client.stop_workflow_executions('invalid', 'invalid')
