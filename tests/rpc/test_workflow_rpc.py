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

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.action import TaskAction
from ai_flow.model.internal.conditions import SingleEventCondition
from ai_flow.model.internal.events import TaskStatusChangedEvent
from ai_flow.operators.bash import BashOperator
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.status import TaskStatus
from ai_flow.model.workflow import Workflow
from ai_flow.rpc.client.aiflow_client import get_scheduler_client
from ai_flow.rpc.server.server import AIFlowServer
from tests.test_utils.mock_utils import MockNotificationClient
from tests.test_utils.unittest_base import BaseUnitTest


class TestWorkflowRpc(BaseUnitTest):
    def setUp(self) -> None:
        super().setUp()
        with mock.patch("ai_flow.task_executor.common.task_executor_base.HeartbeatManager"):
            with mock.patch('ai_flow.rpc.service.scheduler_service.get_notification_client', MockNotificationClient):
                with mock.patch('ai_flow.task_executor.common.task_executor_base.get_notification_client'):
                    self.server = AIFlowServer()
                    self.server.run(is_block=False)
        self.client = get_scheduler_client()
        self.rule_extractor = self.server.scheduler_service.scheduler.dispatcher.rule_extractor

    def tearDown(self) -> None:
        self.server.stop()
        super().tearDown()

    def prepare_workflow(self, workflow_name, namespace='default'):
        if self.client.get_namespace(namespace) is None:
            self.client.add_namespace(namespace)
        with Workflow(name=workflow_name) as workflow:
            op1 = BashOperator(name='bash1', bash_command='echo 1')
            op2 = BashOperator(name='bash2', bash_command='echo 2')
            op2.action_on_task_status(TaskAction.START, upstream_task_status_dict={op1: TaskStatus.SUCCESS})
        workflow_meta = self.client.add_workflow(workflow.name, 'default', 'mock_content', cloudpickle.dumps(workflow))
        rule = WorkflowRule(SingleEventCondition('key1'))
        self.client.add_workflow_trigger(namespace=workflow_meta.namespace,
                                         workflow_name=workflow_meta.name,
                                         rule=cloudpickle.dumps(rule))
        return workflow_meta, workflow

    def test_add_workflow(self):
        workflow_meta, workflow = self.prepare_workflow('workflow1')
        self.assertEqual(workflow.name, workflow_meta.name)
        self.assertEqual(workflow.namespace, workflow_meta.namespace)
        self.assertTrue(workflow_meta.is_enabled)
        self.assertEqual(-1, workflow_meta.event_offset)
        self.assertEqual(cloudpickle.dumps(workflow), workflow_meta.workflow_object)
        self.assertEqual(
            cloudpickle.dumps(self.rule_extractor.workflow_dict[workflow_meta.id]), workflow_meta.workflow_object)
        self.assertEqual({('default', '[task_status_change].default.workflow1.bash1'): {1}},
                         self.rule_extractor.event_workflow_index.task_rule_index)
        self.assertEqual({('default', 'key1'): {1}},
                         self.rule_extractor.event_workflow_index.workflow_rule_index)

    def test_rollback_adding_invalid_workflow(self):
        with self.assertRaises(AIFlowException):
            self.client.add_workflow('workflow', 'default', 'mock_content', b'invalid')
        self.assertEqual('default', self.client.get_namespace('default').name)
        self.assertIsNone(self.client.get_workflow('workflow', 'namespace'))

    def test_get_workflow(self):
        _, workflow = self.prepare_workflow('workflow1')
        workflow_meta = self.client.get_workflow(workflow.name, workflow.namespace)

        self.assertEqual(workflow.name, workflow_meta.name)
        self.assertEqual(workflow.namespace, workflow_meta.namespace)
        self.assertTrue(workflow_meta.is_enabled)
        self.assertEqual(-1, workflow_meta.event_offset)
        self.assertEqual(cloudpickle.dumps(workflow), workflow_meta.workflow_object)

    def test_update_workflow(self):
        self.prepare_workflow('workflow1')
        with Workflow(name='workflow1') as workflow:
            op1 = BashOperator(name='bash3', bash_command='echo 1')
            op2 = BashOperator(name='bash4', bash_command='echo 2')
            op2.action_on_task_status(TaskAction.START, upstream_task_status_dict={op1: TaskStatus.SUCCESS})
        workflow_meta = self.client.update_workflow(workflow.name, workflow.namespace, 'new_content',
                                                    cloudpickle.dumps(workflow), True)
        self.assertEqual('new_content', workflow_meta.content)
        self.assertEqual(cloudpickle.dumps(workflow), workflow_meta.workflow_object)
        self.assertEqual(
            cloudpickle.dumps(self.rule_extractor.workflow_dict[workflow_meta.id]), workflow_meta.workflow_object)
        self.assertEqual({('default', '[task_status_change].default.workflow1.bash3'): {1}},
                         self.rule_extractor.event_workflow_index.task_rule_index)
        self.assertEqual({('default', 'key1'): {1}},
                         self.rule_extractor.event_workflow_index.workflow_rule_index)

    def test_update_non_exists_workflow(self):
        with self.assertRaisesRegex(AIFlowException, r'Workflow invalid.invalid not exists'):
            self.client.update_workflow('invalid', 'invalid', 'content', b'invalid', True)

    def test_rollback_updating_workflow(self):
        _, workflow = self.prepare_workflow('workflow1')
        with self.assertRaises(AIFlowException):
            self.client.update_workflow(workflow.name, workflow.namespace, 'new_content', b'invalid', True)
        workflow_meta = self.client.get_workflow(workflow.name, workflow.namespace)
        self.assertTrue(isinstance(cloudpickle.loads(workflow_meta.workflow_object), Workflow))

    def test_disable_and_enable_workflow(self):
        _, workflow = self.prepare_workflow('workflow1')
        self.client.disable_workflow(workflow.name, workflow.namespace)
        workflow_meta = self.client.get_workflow(workflow.name, workflow.namespace)
        self.assertFalse(workflow_meta.is_enabled)
        self.assertEqual({}, self.rule_extractor.workflow_dict)
        self.assertEqual({}, self.rule_extractor.event_workflow_index.task_rule_index)
        self.assertEqual({}, self.rule_extractor.event_workflow_index.workflow_rule_index)

        self.client.enable_workflow(workflow.name, workflow.namespace)
        workflow_meta = self.client.get_workflow(workflow.name, workflow.namespace)
        self.assertTrue(workflow_meta.is_enabled)
        self.assertEqual(1, len(self.rule_extractor.workflow_dict))
        self.assertEqual({('default', '[task_status_change].default.workflow1.bash1'): {1}},
                         self.rule_extractor.event_workflow_index.task_rule_index)
        self.assertEqual({('default', 'key1'): {1}},
                         self.rule_extractor.event_workflow_index.workflow_rule_index)

    def test_rollback_disable_workflow(self):
        _, workflow = self.prepare_workflow('workflow1')
        self.rule_extractor.workflow_dict = None
        with self.assertRaises(AIFlowException):
            self.client.disable_workflow(workflow.name, workflow.namespace)
        self.assertTrue(self.client.get_workflow(workflow.name, workflow.namespace).is_enabled)

    def test_rollback_enable_workflow(self):
        _, workflow = self.prepare_workflow('workflow1')
        self.client.disable_workflow(workflow.name, workflow.namespace)
        self.assertFalse(self.client.get_workflow(workflow.name, workflow.namespace).is_enabled)
        self.rule_extractor.workflow_dict = None
        with self.assertRaises(AIFlowException):
            self.client.enable_workflow(workflow.name, workflow.namespace)
        self.assertFalse(self.client.get_workflow(workflow.name, workflow.namespace).is_enabled)

    def test_list_workflows(self):
        self.prepare_workflow('workflow1')
        self.prepare_workflow('workflow2')
        self.prepare_workflow('workflow3')
        workflows = self.client.list_workflows(namespace='default')
        self.assertEqual(3, len(workflows))

        workflows = self.client.list_workflows('default', page_size=2, offset=1)
        self.assertEqual(2, len(workflows))
        self.assertEqual('workflow2', workflows[0].name)
        self.assertEqual('workflow3', workflows[1].name)
        self.assertIsNone(self.client.list_workflows('non-exists-namespace'))
        self.assertEqual(3, len(self.rule_extractor.workflow_dict))

    def test_delete_workflow(self):
        self.prepare_workflow('workflow1')
        self.prepare_workflow('workflow2')
        prefix = TaskStatusChangedEvent.event_key_prefix()
        self.assertEqual({
            ('default', f'{prefix}.default.workflow1.bash1'): {1},
            ('default', f'{prefix}.default.workflow2.bash1'): {2}
        }, self.rule_extractor.event_workflow_index.task_rule_index)
        self.assertEqual({
            ('default', 'key1'): {1, 2}
        }, self.rule_extractor.event_workflow_index.workflow_rule_index)

        self.client.delete_workflow(name='workflow2', namespace='default')
        workflows = self.client.list_workflows('default')
        self.assertEqual(1, len(workflows))
        self.assertEqual(1, len(self.rule_extractor.workflow_dict))
        self.assertEqual({
            ('default', '[task_status_change].default.workflow1.bash1'): {1}
        }, self.rule_extractor.event_workflow_index.task_rule_index)
        self.assertEqual({
            ('default', 'key1'): {1}
        }, self.rule_extractor.event_workflow_index.workflow_rule_index)

    def test_delete_non_exists_workflow(self):
        with self.assertRaisesRegex(AIFlowException, r"Workflow default.non-exists not exists"):
            self.client.delete_workflow(name='non-exists', namespace='default')

    def test_disable_non_exists_workflow(self):
        with self.assertRaisesRegex(AIFlowException, r"Workflow default.non-exists not exists"):
            self.client.disable_workflow(name='non-exists', namespace='default')

    def test_enable_non_exists_workflow(self):
        with self.assertRaisesRegex(AIFlowException, r"Workflow default.non-exists not exists"):
            self.client.enable_workflow(name='non-exists', namespace='default')
