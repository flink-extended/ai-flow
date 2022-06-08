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
import json
import unittest

import cloudpickle
from notification_service.event import Event, EventKey

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.internal.events import EventContextConstant
from ai_flow.model.operator import Operator
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.status import WorkflowStatus
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.rule_extractor import gen_all_combination, gen_all_tuple_by_event_key, \
    workflow_expect_event_tuples, build_task_rule_index, RuleExtractor
from tests.scheduler.test_utils import UnitTestWithNamespace


class TestRuleExtractorUtil(unittest.TestCase):

    def test_gen_all_combination(self):
        a = [1, None, 3, None]
        results = gen_all_combination(a)
        self.assertEqual(4, len(results))
        self.assertTrue((1, None, 3, None) in results)
        self.assertTrue((1, None, None, None) in results)
        self.assertTrue((None, None, 3, None) in results)
        self.assertTrue((None, None, None, None) in results)

        a = [1, 2, 3, None]
        self.assertEqual(8, len(gen_all_combination(a)))

        a = [1, 2, 3, 4]
        self.assertEqual(16, len(gen_all_combination(a)))

    def test_gen_all_tuple_by_event_key(self):
        a = EventKey(namespace='1', name=None, event_type='3', sender=None)
        results = gen_all_tuple_by_event_key(a)
        self.assertEqual(4, len(results))
        self.assertTrue(('1', None, '3', None) in results)
        self.assertTrue(('1', None, None, None) in results)
        self.assertTrue((None, None, '3', None) in results)
        self.assertTrue((None, None, None, None) in results)

        a = EventKey(namespace='1', name='2', event_type='3', sender=None)
        self.assertEqual(8, len(gen_all_tuple_by_event_key(a)))

        a = EventKey(namespace='1', name='2', event_type='3', sender='4')
        self.assertEqual(16, len(gen_all_tuple_by_event_key(a)))

    def test_parse_expect_keys(self):
        with Workflow(name='workflow') as workflow:
            o1 = Operator(name='op')
            o1.action_on_condition(action=TaskAction.START,
                                   condition=Condition(
                                       expect_events=[EventKey(namespace='namespace',
                                                               name='event_1',
                                                               event_type='event_type',
                                                               sender='sender'
                                                               ),
                                                      EventKey(namespace='namespace',
                                                               name='event_2',
                                                               event_type='event_type',
                                                               sender='sender'
                                                               ),
                                                      EventKey(namespace='namespace',
                                                               name='event_2',
                                                               event_type='event_type',
                                                               sender='sender'
                                                               )
                                                      ]))
        expect_keys = workflow_expect_event_tuples(workflow=workflow)
        self.assertEqual(2, len(expect_keys))

    def test_build_task_rule_index(self):
        workflow_dict = self.build_workflow_dict_1()
        task_rule_index = build_task_rule_index(workflow_dict=workflow_dict)
        self.assertEqual(1, len(task_rule_index[('namespace', 'event_2_0', None, 'sender')]))
        self.assertEqual(3, len(task_rule_index[('namespace', 'event_1', 'event_type', 'sender')]))
        self.assertEqual(3, len(task_rule_index[('namespace', 'event_4', 'event_type', None)]))

    @staticmethod
    def build_workflow_dict_1():
        workflow_dict = {}
        for i in range(3):
            with Workflow(name='workflow_'.format(i + 1)) as workflow:
                o1 = Operator(name='op_1')
                o2 = Operator(name='op_2')

                o1.action_on_condition(action=TaskAction.START,
                                       condition=Condition(
                                           expect_events=[EventKey(namespace='namespace',
                                                                   name='event_1',
                                                                   event_type='event_type',
                                                                   sender='sender'
                                                                   ),
                                                          EventKey(namespace='namespace',
                                                                   name='event_2_{}'.format(i),
                                                                   event_type=None,
                                                                   sender='sender'
                                                                   )
                                                          ]))
                o2.action_on_condition(action=TaskAction.START,
                                       condition=Condition(
                                           expect_events=[EventKey(namespace='namespace',
                                                                   name='event_3_{}'.format(i),
                                                                   event_type='event_type',
                                                                   sender=None
                                                                   ),
                                                          EventKey(namespace='namespace',
                                                                   name='event_4',
                                                                   event_type='event_type',
                                                                   sender=None
                                                                   )
                                                          ]))
                workflow_dict[i + 1] = workflow
        return workflow_dict


class TestRuleExtractor(UnitTestWithNamespace):

    def test_extract_workflow_rules(self):
        def build_workflows():
            for i in range(3):
                with Workflow(name='workflow_{}'.format(i)) as workflow:
                    o1 = Operator(name='op')
                workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                                   name=workflow.name,
                                                                   content='',
                                                                   workflow_object=cloudpickle.dumps(workflow))
                self.metadata_manager.flush()
                expect_events_1 = [EventKey(namespace='namespace',
                                            name='event_1',
                                            event_type='event_type',
                                            sender='sender'
                                            ),
                                   EventKey(namespace='namespace',
                                            name='event_1_{}'.format(i),
                                            event_type=None,
                                            sender='sender'
                                            ),
                                   EventKey(namespace='namespace',
                                            name='event',
                                            event_type=None,
                                            sender='sender'
                                            )
                                   ]
                expect_events_2 = [EventKey(namespace='namespace',
                                            name='event_2',
                                            event_type='event_type',
                                            sender='sender'
                                            ),
                                   EventKey(namespace='namespace',
                                            name='event_2_{}'.format(i),
                                            event_type=None,
                                            sender='sender'
                                            ),
                                   EventKey(namespace='namespace',
                                            name='event',
                                            event_type=None,
                                            sender='sender'
                                            )
                                   ]
                self.metadata_manager.add_workflow_trigger(workflow_id=workflow_meta.id,
                                                           rule=cloudpickle.dumps(WorkflowRule(condition=Condition(
                                                               expect_events=expect_events_1))))
                self.metadata_manager.flush()
                self.metadata_manager.add_workflow_trigger(workflow_id=workflow_meta.id,
                                                           rule=cloudpickle.dumps(WorkflowRule(condition=Condition(
                                                               expect_events=expect_events_2))))
                self.metadata_manager.flush()

        build_workflows()

        rule_extractor = RuleExtractor(metadata_manager=self.metadata_manager)

        event = Event(event_key=EventKey(namespace='namespace',
                                         name='event_1',
                                         event_type='event_type',
                                         sender='sender'), message='')
        results = rule_extractor.extract_workflow_rules(event=event)
        self.metadata_manager.flush()
        self.assertEqual(3, len(results))
        for r in results:
            self.assertEqual(1, len(r.rules))

        event = Event(event_key=EventKey(namespace='namespace',
                                         name='event',
                                         event_type='event_type',
                                         sender='sender'), message='')
        results = rule_extractor.extract_workflow_rules(event=event)
        self.metadata_manager.flush()
        self.assertEqual(3, len(results))
        for r in results:
            self.assertEqual(2, len(r.rules))

    def test_extract_workflow_execution_rules(self):
        def build_workflows():
            for i in range(3):
                expect_events_1 = [EventKey(namespace='namespace',
                                            name='event_1',
                                            event_type='event_type',
                                            sender='sender'
                                            ),
                                   EventKey(namespace='namespace',
                                            name='event_1_{}'.format(i),
                                            event_type=None,
                                            sender='sender'
                                            ),
                                   EventKey(namespace='namespace',
                                            name='event',
                                            event_type=None,
                                            sender='sender'
                                            )
                                   ]
                expect_events_2 = [EventKey(namespace='namespace',
                                            name='event_2',
                                            event_type='event_type',
                                            sender='sender'
                                            ),
                                   EventKey(namespace='namespace',
                                            name='event_2_{}'.format(i),
                                            event_type=None,
                                            sender='sender'
                                            ),
                                   EventKey(namespace='namespace',
                                            name='event',
                                            event_type=None,
                                            sender='sender'
                                            )
                                   ]
                with Workflow(name='workflow_{}'.format(i)) as workflow:
                    op_1 = Operator(name='op_1')
                    op_2 = Operator(name='op_2')

                    op_1.action_on_condition(action=TaskAction.START,
                                             condition=Condition(expect_events=expect_events_1))
                    op_2.action_on_condition(action=TaskAction.START,
                                             condition=Condition(expect_events=expect_events_2))

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
                        self.metadata_manager.update_workflow_execution_status(
                            workflow_execution_id=workflow_execution_meta.id,
                            status=WorkflowStatus.RUNNING.value
                        )
                        self.metadata_manager.flush()

        build_workflows()

        rule_extractor = RuleExtractor(metadata_manager=self.metadata_manager)

        event = Event(event_key=EventKey(namespace='namespace',
                                         name='event_1',
                                         event_type='event_type',
                                         sender='sender'), message='')
        results = rule_extractor.extract_workflow_execution_rules(event=event)
        self.metadata_manager.flush()
        self.assertEqual(6, len(results))
        for r in results:
            self.assertEqual(1, len(r.task_rule_wrappers))

        event = Event(event_key=EventKey(namespace='namespace',
                                         name='event',
                                         event_type='event_type',
                                         sender='sender'), message='')
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
