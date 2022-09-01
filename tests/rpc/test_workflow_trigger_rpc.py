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
from ai_flow.model.internal.conditions import SingleEventCondition
from ai_flow.operators.bash import BashOperator
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.workflow import Workflow
from ai_flow.rpc.client.aiflow_client import get_scheduler_client
from ai_flow.rpc.server.server import AIFlowServer
from tests.test_utils.mock_utils import MockNotificationClient
from tests.test_utils.unittest_base import BaseUnitTest


class TestWorkflowTriggerRpc(BaseUnitTest):
    def setUp(self) -> None:
        super().setUp()
        with mock.patch("ai_flow.task_executor.common.task_executor_base.HeartbeatManager"):
            with mock.patch('ai_flow.task_executor.common.task_executor_base.get_notification_client'):
                with mock.patch('ai_flow.rpc.service.scheduler_service.get_notification_client', MockNotificationClient):
                    self.server = AIFlowServer()
                    self.server.run(is_block=False)
        self.client = get_scheduler_client()
        self.rule_extractor = self.server.scheduler_service.scheduler.dispatcher.rule_extractor
        self.workflow_meta = self.prepare_workflow()
        self.rule1 = WorkflowRule(SingleEventCondition('key1'))
        self.rule2 = WorkflowRule(SingleEventCondition('key2'))

    def tearDown(self) -> None:
        self.server.stop()
        super().tearDown()

    def prepare_workflow(self):
        with Workflow(name='workflow1') as workflow:
            BashOperator(name='bash', bash_command='echo 1')
        workflow_meta = self.client.add_workflow(workflow.name, 'default', 'mock_content', cloudpickle.dumps(workflow))
        return workflow_meta

    def test_add_workflow_trigger(self):
        trigger = self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                                   workflow_name=self.workflow_meta.name,
                                                   rule=cloudpickle.dumps(self.rule1))
        self.assertEqual(1, trigger.id)
        self.assertEqual(self.workflow_meta.id, trigger.workflow_id)
        self.assertFalse(trigger.is_paused)
        self.assertEqual(cloudpickle.dumps(self.rule1), trigger.rule)
        self.assertIsNotNone(trigger.create_time)
        self.assertEqual(1, len(self.rule_extractor.workflow_trigger_dict))
        self.assertEqual(1, self.rule_extractor.workflow_trigger_dict[1].id)
        self.assertEqual({('default', 'key1'): {1}},
                         self.rule_extractor.event_workflow_index.workflow_rule_index)

    def test_get_workflow_trigger(self):
        trigger = self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                                   workflow_name=self.workflow_meta.name,
                                                   rule=cloudpickle.dumps(self.rule1))
        retrieved_trigger = self.client.get_workflow_trigger(trigger.id)
        self.assertEqual(trigger.id, retrieved_trigger.id)
        self.assertEqual(trigger.workflow_id, retrieved_trigger.workflow_id)
        self.assertEqual(trigger.is_paused, retrieved_trigger.is_paused)
        self.assertEqual(trigger.rule, retrieved_trigger.rule)
        self.assertEqual(trigger.create_time, retrieved_trigger.create_time)

    def test_get_non_exists_workflow_trigger(self):
        self.assertIsNone(self.client.get_workflow_trigger(101))

    def test_list_workflow_triggers(self):
        self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                         workflow_name=self.workflow_meta.name,
                                         rule=cloudpickle.dumps(self.rule1))
        self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                         workflow_name=self.workflow_meta.name,
                                         rule=cloudpickle.dumps(self.rule2))
        triggers = self.client.list_workflow_triggers(self.workflow_meta.namespace, self.workflow_meta.name)
        self.assertEqual(2, len(triggers))
        self.assertEqual(cloudpickle.dumps(self.rule1), triggers[0].rule)
        self.assertEqual(cloudpickle.dumps(self.rule2), triggers[1].rule)

        second = self.client.list_workflow_triggers(
            self.workflow_meta.namespace, self.workflow_meta.name, page_size=1, offset=1)[0]
        self.assertEqual(cloudpickle.dumps(self.rule2), second.rule)

    def test_list_non_exists_workflow_triggers(self):
        with self.assertRaisesRegex(AIFlowException, r'Workflow invalid.invalid not exists'):
            self.client.list_workflow_executions('invalid', 'invalid')

    def test_delete_workflow_trigger(self):
        trigger = self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                                   workflow_name=self.workflow_meta.name,
                                                   rule=cloudpickle.dumps(self.rule1))
        self.assertEqual(1, len(self.client.list_workflow_triggers(self.workflow_meta.namespace,
                                                                   self.workflow_meta.name)))
        self.assertEqual(1, len(self.rule_extractor.workflow_trigger_dict))
        self.assertEqual(1, len(self.rule_extractor.event_workflow_index.workflow_rule_index))

        self.assertTrue(self.client.delete_workflow_trigger(trigger.id))
        self.assertIsNone(self.client.list_workflow_triggers(self.workflow_meta.namespace,
                                                             self.workflow_meta.name))
        self.assertEqual(0, len(self.rule_extractor.workflow_trigger_dict))
        self.assertEqual(0, len(self.rule_extractor.event_workflow_index.workflow_rule_index))

    def test_delete_non_exists_workflow_trigger(self):
        with self.assertRaisesRegex(AIFlowException, r"Workflow trigger 101 not exists"):
            self.client.delete_workflow_trigger(101)

    def test_delete_workflow_triggers(self):
        self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                         workflow_name=self.workflow_meta.name,
                                         rule=cloudpickle.dumps(self.rule1))
        self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                         workflow_name=self.workflow_meta.name,
                                         rule=cloudpickle.dumps(self.rule2))
        triggers = self.client.list_workflow_triggers(self.workflow_meta.namespace, self.workflow_meta.name)
        self.assertEqual(2, len(triggers))
        self.assertEqual(2, len(self.rule_extractor.workflow_trigger_dict))
        self.assertEqual(2, len(self.rule_extractor.event_workflow_index.workflow_rule_index))

        self.client.delete_workflow_triggers(self.workflow_meta.namespace, self.workflow_meta.name)
        triggers = self.client.list_workflow_triggers(self.workflow_meta.namespace, self.workflow_meta.name)
        self.assertIsNone(triggers)
        self.assertEqual(0, len(self.rule_extractor.workflow_trigger_dict))
        self.assertEqual(0, len(self.rule_extractor.event_workflow_index.workflow_rule_index))

    def test_rollback_deleting_workflow_trigger(self):
        trigger = self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                                   workflow_name=self.workflow_meta.name,
                                                   rule=cloudpickle.dumps(self.rule1))
        self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                         workflow_name=self.workflow_meta.name,
                                         rule=cloudpickle.dumps(self.rule2))
        print(self.rule_extractor.event_workflow_index.workflow_rule_index)
        self.rule_extractor.workflow_trigger_dict.clear()
        print(self.rule_extractor.event_workflow_index.workflow_rule_index)
        with self.assertRaises(AIFlowException):
            self.assertTrue(self.client.delete_workflow_trigger(trigger.id))
        self.assertEqual(2, len(self.client.list_workflow_triggers(namespace=self.workflow_meta.namespace,
                                                                   workflow_name=self.workflow_meta.name)))
        with self.assertRaises(AIFlowException):
            self.assertTrue(self.client.delete_workflow_triggers(namespace=self.workflow_meta.namespace,
                                                                 workflow_name=self.workflow_meta.name))
        self.assertEqual(2, len(self.client.list_workflow_triggers(namespace=self.workflow_meta.namespace,
                                                                   workflow_name=self.workflow_meta.name)))

    def test_pause_and_resume_workflow_trigger(self):
        trigger = self.client.add_workflow_trigger(namespace=self.workflow_meta.namespace,
                                                   workflow_name=self.workflow_meta.name,
                                                   rule=cloudpickle.dumps(self.rule1))
        self.assertFalse(trigger.is_paused)
        self.assertEqual(1, len(self.rule_extractor.workflow_trigger_dict))
        self.assertEqual(1, len(self.rule_extractor.event_workflow_index.workflow_rule_index))

        self.client.pause_workflow_trigger(trigger.id)
        self.assertTrue(self.client.get_workflow_trigger(trigger.id).is_paused)
        self.assertEqual(0, len(self.rule_extractor.workflow_trigger_dict))
        self.assertEqual(0, len(self.rule_extractor.event_workflow_index.workflow_rule_index))

        self.client.resume_workflow_trigger(trigger.id)
        self.assertFalse(self.client.get_workflow_trigger(trigger.id).is_paused)
        self.assertEqual(1, len(self.rule_extractor.workflow_trigger_dict))
        self.assertEqual(1, len(self.rule_extractor.event_workflow_index.workflow_rule_index))

    def test_pause_and_resume_non_exists_workflow_trigger(self):
        with self.assertRaisesRegex(AIFlowException, r"Workflow trigger 101 not exists"):
            self.client.pause_workflow_trigger(101)
        with self.assertRaisesRegex(AIFlowException, r"Workflow trigger 101 not exists"):
            self.client.resume_workflow_trigger(101)
