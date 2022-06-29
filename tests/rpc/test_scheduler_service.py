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
from unittest import mock

import cloudpickle

from ai_flow.model.operators.bash import BashOperator
from ai_flow.model.workflow import Workflow
from ai_flow.rpc.client.aiflow_client import get_ai_flow_client
from ai_flow.rpc.server.server import AIFlowServer
from tests.test_utils.unittest_base import BaseUnitTest


class TestSchedulerService(BaseUnitTest):
    def setUp(self) -> None:
        super().setUp()
        with mock.patch("ai_flow.task_executor.common.task_executor_base.HeartbeatManager"):
            with mock.patch('ai_flow.rpc.service.scheduler_service.EmbeddedNotificationClient'):
                self.server = AIFlowServer()
                self.server.run(is_block=False)
        self.client = get_ai_flow_client()

    def tearDown(self) -> None:
        self.server.stop()
        super().tearDown()

    def test_workflow_operation(self):
        self.client.add_namespace('default')
        with Workflow(name='workflow1') as workflow:
            BashOperator(name='bash', bash_command='echo 1')
        workflow_meta = self.client.add_workflow(workflow.name, 'default', 'mock_content', cloudpickle.dumps(workflow))
        self.assertEqual('workflow1', workflow_meta.name)
        self.assertEqual('default', workflow_meta.namespace)
        self.assertTrue(workflow_meta.is_enabled)
        self.assertEqual(-1, workflow_meta.event_offset)
        self.assertEqual(cloudpickle.dumps(workflow), workflow_meta.workflow_object)
        self.assertEqual(
            cloudpickle.dumps(
                self.server.scheduler_service.scheduler.dispatcher.rule_extractor.workflow_dict[workflow_meta.id]
            ), workflow_meta.workflow_object
        )

        workflow_meta = self.client.get_workflow(workflow.name, 'default')
        self.assertEqual('workflow1', workflow_meta.name)
        self.assertEqual('default', workflow_meta.namespace)
        self.assertTrue(workflow_meta.is_enabled)
        self.assertEqual(-1, workflow_meta.event_offset)
        self.assertEqual(cloudpickle.dumps(workflow), workflow_meta.workflow_object)

        workflow_meta = self.client.update_workflow(workflow.name, 'default', 'new_content',
                                                    cloudpickle.dumps(workflow), False)
        self.assertFalse(workflow_meta.is_enabled)
        self.assertEqual(
                0, len(self.server.scheduler_service.scheduler.dispatcher.rule_extractor.workflow_dict))

        self.client.enable_workflow(workflow.name, 'default')
        workflow_meta = self.client.get_workflow(workflow.name, 'default')
        self.assertTrue(workflow_meta.is_enabled)
        self.assertEqual(
            cloudpickle.dumps(
                self.server.scheduler_service.scheduler.dispatcher.rule_extractor.workflow_dict[workflow_meta.id]
            ), workflow_meta.workflow_object
        )
        self.client.disable_workflow(workflow.name, 'default')
        workflow_meta = self.client.get_workflow(workflow.name, 'default')
        self.assertFalse(workflow_meta.is_enabled)
        self.assertEqual(
            0, len(self.server.scheduler_service.scheduler.dispatcher.rule_extractor.workflow_dict))

        self.client.add_workflow('workflow2', 'default', 'mock_content', cloudpickle.dumps(workflow))
        self.client.add_workflow('workflow3', 'default', 'mock_content', cloudpickle.dumps(workflow))
        workflows = self.client.list_workflows('default')
        self.assertEqual(3, len(workflows))

        workflows = self.client.list_workflows('default', page_size=2, offset=1)
        self.assertEqual(2, len(workflows))
        self.assertEqual('workflow2', workflows[0].name)
        self.assertEqual('workflow3', workflows[1].name)
        self.assertIsNone(self.client.list_workflows('non-exists-namespace'))
        self.assertEqual(
            2, len(self.server.scheduler_service.scheduler.dispatcher.rule_extractor.workflow_dict))

        self.assertTrue(self.client.delete_workflow(name='workflow2', namespace='default'))
        workflows = self.client.list_workflows('default')
        self.assertEqual(2, len(workflows))
        self.assertEqual(
            1, len(self.server.scheduler_service.scheduler.dispatcher.rule_extractor.workflow_dict))
        self.assertTrue(self.client.delete_workflow(name='workflow1', namespace='default'))
        self.assertEqual(
            1, len(self.server.scheduler_service.scheduler.dispatcher.rule_extractor.workflow_dict))
        self.assertFalse(self.client.delete_workflow(name='non-exists', namespace='default'))
