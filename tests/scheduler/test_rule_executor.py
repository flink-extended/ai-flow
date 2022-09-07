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
import unittest
from typing import List

import cloudpickle
from notification_service.model.event import Event

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.operator import Operator
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.state import ValueStateDescriptor, ValueState
from ai_flow.model.status import WorkflowStatus, TaskStatus
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.rule_executor import RuleExecutor
from ai_flow.scheduler.rule_extractor import RuleExtractor
from tests.scheduler.test_utils import UnitTestWithNamespace


class SimpleCondition(Condition):

    def __init__(self, expect_event_keys: List[str], flag):
        super().__init__(expect_event_keys)
        self.flag = flag

    def is_met(self, event: Event, context: Context) -> bool:
        return self.flag


class StateCondition(Condition):

    def is_met(self, event: Event, context: Context) -> bool:
        state: ValueState = context.get_state(ValueStateDescriptor(name='count'))
        v = state.value()
        if v is None:
            v = 0
        v = v + 1
        state.update(v)
        if 0 == v % 2:
            return True
        else:
            return False


class TestRuleExecutor(UnitTestWithNamespace):

    def _build_workflow_execution(self):
        with Workflow(name='workflow', namespace=self.namespace_name) as workflow:
            op_1 = Operator(name='op_1')
            op_2 = Operator(name='op_2')
            op_3 = Operator(name='op_3')
            op_4 = Operator(name='op_4')
            op_5 = Operator(name='op_5')

            op_1.action_on_condition(action=TaskAction.START,
                                     condition=SimpleCondition(expect_event_keys=['event_1'], flag=True))
            op_2.action_on_condition(action=TaskAction.START,
                                     condition=SimpleCondition(expect_event_keys=['event_2'], flag=False))
            op_3.action_on_condition(action=TaskAction.STOP,
                                     condition=SimpleCondition(expect_event_keys=['event_3'], flag=True))
            op_4.action_on_condition(action=TaskAction.RESTART,
                                     condition=SimpleCondition(expect_event_keys=['event_4'], flag=True))
            op_5.action_on_condition(action=TaskAction.RESTART,
                                     condition=StateCondition(expect_event_keys=['event_5']))

        workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                           name=workflow.name,
                                                           content='',
                                                           workflow_object=cloudpickle.dumps(workflow))
        self.metadata_manager.flush()
        snapshot_meta = self.metadata_manager.add_workflow_snapshot(
            workflow_id=workflow_meta.id,
            workflow_object=workflow_meta.workflow_object,
            uri='url',
            signature='')
        self.metadata_manager.flush()
        workflow_execution_meta = self.metadata_manager.add_workflow_execution(
            workflow_id=workflow_meta.id,
            run_type=ExecutionType.MANUAL,
            snapshot_id=snapshot_meta.id)
        self.metadata_manager.flush()
        self.metadata_manager.update_workflow_execution(
            workflow_execution_id=workflow_execution_meta.id,
            status=WorkflowStatus.RUNNING.value)
        self.metadata_manager.flush()
        task_execution_meta = self.metadata_manager.add_task_execution(
            workflow_execution_id=workflow_execution_meta.id,
            task_name='op_1')
        self.metadata_manager.flush()
        self.metadata_manager.update_task_execution(task_execution_id=task_execution_meta.id, status=TaskStatus.SUCCESS)
        self.metadata_manager.flush()
        self.metadata_manager.add_task_execution(workflow_execution_id=workflow_execution_meta.id, task_name='op_3')
        self.metadata_manager.flush()
        self.metadata_manager.add_task_execution(workflow_execution_id=workflow_execution_meta.id, task_name='op_4')
        self.metadata_manager.flush()

    def test_execute_workflow_execution_rule(self):
        self._build_workflow_execution()

        event = Event(key='event_1', value='')
        event.namespace = self.namespace_name
        result = self.exec_event_on_workflow_execution(event)
        self.assertEqual(1, len(result.task_schedule_commands))
        self.assertEqual('op_1', result.task_schedule_commands[0].new_task_execution.task_name)
        self.assertEqual(2, result.task_schedule_commands[0].new_task_execution.seq_num)
        self.assertEqual(None, result.task_schedule_commands[0].current_task_execution)
        self.assertEqual(TaskAction.START, result.task_schedule_commands[0].action)

        event = Event(key='event_2', value='')
        event.namespace = self.namespace_name
        result = self.exec_event_on_workflow_execution(event)
        self.assertIsNone(result)

        event = Event(key='event_3', value='')
        event.namespace = self.namespace_name
        result = self.exec_event_on_workflow_execution(event)
        self.assertEqual(1, len(result.task_schedule_commands))
        self.assertEqual('op_3', result.task_schedule_commands[0].current_task_execution.task_name)
        self.assertEqual(1, result.task_schedule_commands[0].current_task_execution.seq_num)
        self.assertEqual(None, result.task_schedule_commands[0].new_task_execution)
        self.assertEqual(TaskAction.STOP, result.task_schedule_commands[0].action)

        event = Event(key='event_4', value='')
        event.namespace = self.namespace_name
        result = self.exec_event_on_workflow_execution(event)
        self.assertEqual(1, len(result.task_schedule_commands))
        self.assertEqual('op_4', result.task_schedule_commands[0].current_task_execution.task_name)
        self.assertEqual(1, result.task_schedule_commands[0].current_task_execution.seq_num)
        self.assertEqual('op_4', result.task_schedule_commands[0].new_task_execution.task_name)
        self.assertEqual(2, result.task_schedule_commands[0].new_task_execution.seq_num)
        self.assertEqual(TaskAction.RESTART, result.task_schedule_commands[0].action)

        event = Event(key='event_5', value='')
        event.namespace = self.namespace_name
        result = self.exec_event_on_workflow_execution(event)
        self.assertIsNone(result)
        result = self.exec_event_on_workflow_execution(event)
        self.assertEqual(1, len(result.task_schedule_commands))
        result = self.exec_event_on_workflow_execution(event)
        self.assertIsNone(result)

    def exec_event_on_workflow_execution(self, event):
        rule_extractor = RuleExtractor()
        rule_executor = RuleExecutor(metadata_manager=self.metadata_manager)
        results = rule_extractor.extract_workflow_execution_rules(event=event)
        result = rule_executor.execute_workflow_execution_rule(event=event,
                                                               rule=results[0])
        self.metadata_manager.flush()
        return result

    def _build_workflow_trigger(self):
        with Workflow(name='workflow', namespace=self.namespace_name) as workflow:
            op_1 = Operator(name='op_1')

        workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                           name=workflow.name,
                                                           content='',
                                                           workflow_object=cloudpickle.dumps(workflow))
        self.metadata_manager.flush()
        snapshot_meta = self.metadata_manager.add_workflow_snapshot(
            workflow_id=workflow_meta.id,
            workflow_object=workflow_meta.workflow_object,
            uri='url',
            signature='')
        self.metadata_manager.flush()
        workflow_execution_meta = self.metadata_manager.add_workflow_execution(
            workflow_id=workflow_meta.id,
            run_type=ExecutionType.MANUAL,
            snapshot_id=snapshot_meta.id)
        self.metadata_manager.flush()
        self.metadata_manager.update_workflow_execution(
            workflow_execution_id=workflow_execution_meta.id,
            status=WorkflowStatus.RUNNING.value)
        self.metadata_manager.flush()
        self.metadata_manager.add_workflow_trigger(workflow_id=workflow_meta.id,
                                                   rule=cloudpickle.dumps(
                                                       WorkflowRule(
                                                           condition=SimpleCondition(expect_event_keys=['event_1'],
                                                                                     flag=True))))
        self.metadata_manager.flush()
        self.metadata_manager.add_workflow_trigger(workflow_id=workflow_meta.id,
                                                   rule=cloudpickle.dumps(
                                                       WorkflowRule(
                                                           condition=SimpleCondition(expect_event_keys=['event_2'],
                                                                                     flag=False))))
        self.metadata_manager.flush()
        self.metadata_manager.add_workflow_trigger(workflow_id=workflow_meta.id,
                                                   rule=cloudpickle.dumps(
                                                       WorkflowRule(
                                                           condition=SimpleCondition(expect_event_keys=['event_3'],
                                                                                     flag=True))))
        self.metadata_manager.flush()
        self.metadata_manager.add_workflow_trigger(workflow_id=workflow_meta.id,
                                                   rule=cloudpickle.dumps(
                                                       WorkflowRule(
                                                           condition=StateCondition(expect_event_keys=['event_4']))))
        self.metadata_manager.flush()

    def test_execute_workflow_rule(self):
        self._build_workflow_trigger()

        event = Event(key='event_1', value='')
        event.namespace = self.namespace_name
        result = self.exec_event_on_workflow(event)
        self.assertIsNotNone(result)

        event = Event(key='event_2', value='')
        event.namespace = self.namespace_name
        result = self.exec_event_on_workflow(event)
        self.assertIsNone(result)

        event = Event(key='event_3', value='')
        event.namespace = self.namespace_name
        result = self.exec_event_on_workflow(event)
        self.assertIsNotNone(result)

        event = Event(key='event_4', value='')
        event.namespace = self.namespace_name
        result = self.exec_event_on_workflow(event)
        self.assertIsNone(result)
        result = self.exec_event_on_workflow(event)
        self.assertIsNotNone(result)

    def exec_event_on_workflow(self, event):
        rule_extractor = RuleExtractor()
        rule_executor = RuleExecutor(metadata_manager=self.metadata_manager)
        results = rule_extractor.extract_workflow_rules(event=event)
        result = rule_executor.execute_workflow_rule(event=event,
                                                     rule=results[0])
        self.metadata_manager.flush()
        return result


if __name__ == '__main__':
    unittest.main()
