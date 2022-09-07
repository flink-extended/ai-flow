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
import unittest

import cloudpickle
from notification_service.model.event import Event

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.internal.events import EventContextConstant
from ai_flow.model.operator import Operator
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.status import WorkflowStatus, TaskStatus
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.rule_extractor import workflow_expect_event_tuples, build_task_rule_index, RuleExtractor
from tests.scheduler.test_utils import UnitTestWithNamespace


class TestRuleExtractorUtil(unittest.TestCase):

    @staticmethod
    def build_workflow_dict_1():
        workflow_dict = {}
        for i in range(3):
            with Workflow(name='workflow_'.format(i + 1), namespace='namespace') as workflow:
                o1 = Operator(name='op_1')
                o2 = Operator(name='op_2')

                o1.action_on_condition(
                    action=TaskAction.START, condition=Condition(
                        expect_event_keys=['event_1', 'event_2_{}'.format(i),]
                    )
                )
                o2.action_on_condition(
                    action=TaskAction.START, condition=Condition(
                        expect_event_keys=['event_3_{}'.format(i), 'event_4']
                    )
                )
                workflow_dict[i + 1] = workflow
        return workflow_dict

    def test_parse_expect_keys(self):
        with Workflow(name='workflow') as workflow:
            o1 = Operator(name='op')
            o1.action_on_condition(
                action=TaskAction.START, condition=Condition(
                    expect_event_keys=['event_1', 'event_2', 'event_2', ]
                )
            )
        expect_keys = workflow_expect_event_tuples(workflow=workflow)
        self.assertEqual(2, len(expect_keys))

    def test_build_task_rule_index(self):
        workflow_dict = self.build_workflow_dict_1()
        task_rule_index = build_task_rule_index(workflow_dict=workflow_dict)
        self.assertEqual(1, len(task_rule_index[('namespace', 'event_2_0')]))
        self.assertEqual(3, len(task_rule_index[('namespace', 'event_1')]))
        self.assertEqual(3, len(task_rule_index[('namespace', 'event_4')]))


class TestRuleExtractor(UnitTestWithNamespace):

    def test_extract_workflow_rules(self):
        def build_workflows():
            for i in range(3):
                with Workflow(name='workflow_{}'.format(i), namespace=self.namespace_name) as workflow:
                    o1 = Operator(name='op')
                workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                                   name=workflow.name,
                                                                   content='',
                                                                   workflow_object=cloudpickle.dumps(workflow))
                self.metadata_manager.flush()
                expect_events_1 = ['event_1',
                                   'event_1_{}'.format(i),
                                   'event']
                expect_events_2 = ['event_2',
                                   'event_2_{}'.format(i),
                                   'event']
                self.metadata_manager.add_workflow_trigger(workflow_id=workflow_meta.id,
                                                           rule=cloudpickle.dumps(WorkflowRule(condition=Condition(
                                                               expect_event_keys=expect_events_1))))
                self.metadata_manager.flush()
                self.metadata_manager.add_workflow_trigger(workflow_id=workflow_meta.id,
                                                           rule=cloudpickle.dumps(WorkflowRule(condition=Condition(
                                                               expect_event_keys=expect_events_2))))
                self.metadata_manager.flush()

        build_workflows()

        rule_extractor = RuleExtractor()

        event = Event(key='event_1', value='')
        event.namespace = self.namespace_name
        results = rule_extractor.extract_workflow_rules(event=event)
        self.metadata_manager.flush()
        self.assertEqual(3, len(results))
        for r in results:
            self.assertEqual(1, len(r.rules))

        event = Event(key='event', value='')
        event.namespace = self.namespace_name
        results = rule_extractor.extract_workflow_rules(event=event)
        self.metadata_manager.flush()
        self.assertEqual(3, len(results))
        for r in results:
            self.assertEqual(2, len(r.rules))

    def test_extract_workflow_execution_rules(self):
        def build_workflows():
            for i in range(3):
                expect_events_1 = ['event_1',
                                   'event_1_{}'.format(i),
                                   'event']
                expect_events_2 = ['event_2',
                                   'event_2_{}'.format(i),
                                   'event']
                with Workflow(name='workflow_{}'.format(i)) as workflow:
                    op_1 = Operator(name='op_1')
                    op_2 = Operator(name='op_2')
                    op_3 = Operator(name='op_3')

                    op_1.action_on_condition(action=TaskAction.START,
                                             condition=Condition(expect_event_keys=expect_events_1))
                    op_2.action_on_condition(action=TaskAction.START,
                                             condition=Condition(expect_event_keys=expect_events_2))
                    op_3.action_on_task_status(TaskAction.START, {
                        op_1: TaskStatus.SUCCESS, op_2: TaskStatus.SUCCESS
                    })

                workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                                   name=workflow.name,
                                                                   content='',
                                                                   workflow_object=cloudpickle.dumps(workflow))
                self.metadata_manager.flush()
                snapshot_meta = self.metadata_manager.add_workflow_snapshot(
                    workflow_id=workflow_meta.id,
                    workflow_object=workflow_meta.workflow_object,
                    uri='url',
                    signature=str(i))
                self.metadata_manager.flush()
                for j in range(3):
                    workflow_execution_meta = self.metadata_manager.add_workflow_execution(
                        workflow_id=workflow_meta.id,
                        run_type=ExecutionType.MANUAL,
                        snapshot_id=snapshot_meta.id)
                    self.metadata_manager.flush()
                    if 0 == j % 2:
                        self.metadata_manager.update_workflow_execution(
                            workflow_execution_id=workflow_execution_meta.id,
                            status=WorkflowStatus.RUNNING.value
                        )
                        self.metadata_manager.flush()

        build_workflows()

        rule_extractor = RuleExtractor()

        event = Event(key='event_1', value='')
        event.namespace = 'default'
        results = rule_extractor.extract_workflow_execution_rules(event=event)
        self.metadata_manager.flush()
        self.assertEqual(6, len(results))
        for r in results:
            self.assertEqual(1, len(r.task_rule_wrappers))

        event = Event(key='event', value='')
        event.namespace = 'default'
        results = rule_extractor.extract_workflow_execution_rules(event=event)
        self.metadata_manager.flush()
        self.assertEqual(6, len(results))
        for r in results:
            self.assertEqual(2, len(r.task_rule_wrappers))

        event.context = json.dumps({EventContextConstant.WORKFLOW_EXECUTION_ID: 1})
        results = rule_extractor.extract_workflow_execution_rules(event=event)
        self.metadata_manager.flush()
        self.assertEqual(1, len(results))


if __name__ == '__main__':
    unittest.main()
