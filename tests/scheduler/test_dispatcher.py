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

import cloudpickle
from notification_service.model.event import Event

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.internal.events import StartWorkflowExecutionEvent, StartTaskExecutionEvent, \
    StopWorkflowExecutionEvent
from ai_flow.model.operator import Operator
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.status import WorkflowStatus
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.dispatcher import Dispatcher
from ai_flow.scheduler.worker import Worker
from tests.scheduler.test_utils import UnitTestWithNamespace


class TestDispatcher(UnitTestWithNamespace):
    def setUp(self) -> None:
        super().setUp()
        with Workflow(name='workflow', namespace=self.namespace_name) as workflow:
            op = Operator(name='op')
            op.action_on_condition(action=TaskAction.START,
                                   condition=Condition(expect_event_keys=['event_1']))

        self.workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                                name=workflow.name,
                                                                content='',
                                                                workflow_object=cloudpickle.dumps(workflow))
        self.metadata_manager.flush()
        self.workflow_trigger \
            = self.metadata_manager.add_workflow_trigger(workflow_id=self.workflow_meta.id,
                                                         rule=cloudpickle.dumps(
                                                             WorkflowRule(condition=Condition(expect_event_keys=['event_2']))
                                                         ))
        self.metadata_manager.flush()
        self.snapshot_meta = self.metadata_manager.add_workflow_snapshot(
            workflow_id=self.workflow_meta.id,
            workflow_object=self.workflow_meta.workflow_object,
            uri='url',
            signature='')
        self.metadata_manager.flush()
        self.workflow_execution_meta = self.metadata_manager.add_workflow_execution(workflow_id=self.workflow_meta.id,
                                                                                    run_type=ExecutionType.MANUAL,
                                                                                    snapshot_id=self.snapshot_meta.id)
        self.metadata_manager.flush()
        self.metadata_manager.update_workflow_execution(workflow_execution_id=self.workflow_execution_meta.id,
                                                        status=WorkflowStatus.RUNNING)
        self.metadata_manager.flush()

    def test_dispatch(self):
        worker_num = 3
        workers = []
        for i in range(worker_num):
            workers.append(Worker())
        dispatcher = Dispatcher(workers=workers)
        event: Event = StartWorkflowExecutionEvent(workflow_id=self.workflow_meta.id, snapshot_id=self.snapshot_meta.id)
        event.offset = 1
        dispatcher.dispatch(event)
        self.assertEqual(1, workers[1].input_queue.qsize())

        event = StartTaskExecutionEvent(workflow_execution_id=2, task_name='op')
        event.offset = 1
        dispatcher.dispatch(event)
        self.assertEqual(1, workers[2].input_queue.qsize())

        event = Event(key='event_1', value='')
        event.namespace = self.namespace_name
        event.offset = 1
        dispatcher.dispatch(event)
        self.assertEqual(2, workers[1].input_queue.qsize())

        event = Event(key='event_2', value='')
        event.namespace = self.namespace_name
        event.offset = 1
        dispatcher.dispatch(event)
        self.assertEqual(3, workers[1].input_queue.qsize())

    def test__get_max_committed_offset(self):
        self.assertEqual(-1, Dispatcher._get_max_committed_offset())
        self.metadata_manager.set_workflow_event_offset(self.workflow_meta.id, 10)
        self.assertEqual(10, Dispatcher._get_max_committed_offset())
        self.metadata_manager.set_workflow_execution_event_offset(self.workflow_execution_meta.id, 11)
        self.assertEqual(11, Dispatcher._get_max_committed_offset())

    def test_scheduling_event_in_recovery_mode(self):
        worker_num = 3
        workers = []
        for i in range(worker_num):
            workers.append(Worker())
        event1: Event = StartWorkflowExecutionEvent(self.workflow_meta.id, self.snapshot_meta.id)
        event1.offset = 1
        event2: Event = StartWorkflowExecutionEvent(self.workflow_meta.id, self.snapshot_meta.id)
        event2.offset = 2
        event3: Event = StopWorkflowExecutionEvent(self.workflow_execution_meta.id)
        event3.offset = 1
        event4: Event = StopWorkflowExecutionEvent(self.workflow_execution_meta.id)
        event4.offset = 3

        self.metadata_manager.set_workflow_execution_event_offset(self.workflow_execution_meta.id, 2)
        self.metadata_manager.set_workflow_event_offset(self.workflow_meta.id, 1)
        self.metadata_manager.commit()

        dispatcher = Dispatcher(workers=workers)
        dispatcher.dispatch(event1)
        self.assertEqual(0, workers[1].input_queue.qsize())
        dispatcher.dispatch(event2)
        self.assertEqual(1, workers[1].input_queue.qsize())
        dispatcher.dispatch(event3)
        self.assertEqual(1, workers[1].input_queue.qsize())
        dispatcher.dispatch(event4)
        self.assertEqual(2, workers[1].input_queue.qsize())

    def test_non_scheduling_event_in_recovery_mode(self):
        worker_num = 3
        workers = []
        for i in range(worker_num):
            workers.append(Worker())
        event1: Event = Event(key="event_1", value=None)
        event1.namespace = self.namespace_name
        event1.offset = 1
        event2: Event = Event(key="event_1", value=None)
        event2.namespace = self.namespace_name
        event2.offset = 3
        event3: Event = Event(key="event_2", value=None)
        event3.namespace = self.namespace_name
        event3.offset = 1
        event4: Event = Event(key="event_2", value=None)
        event4.namespace = self.namespace_name
        event4.offset = 2

        self.metadata_manager.set_workflow_execution_event_offset(self.workflow_execution_meta.id, 2)
        self.metadata_manager.set_workflow_event_offset(self.workflow_meta.id, 1)
        self.metadata_manager.commit()

        dispatcher = Dispatcher(workers=workers)
        dispatcher.dispatch(event1)
        self.assertEqual(0, workers[1].input_queue.qsize())
        dispatcher.dispatch(event2)
        self.assertEqual(1, workers[1].input_queue.qsize())
        dispatcher.dispatch(event3)
        self.assertEqual(1, workers[1].input_queue.qsize())
        dispatcher.dispatch(event4)
        self.assertEqual(2, workers[1].input_queue.qsize())


if __name__ == '__main__':
    unittest.main()
