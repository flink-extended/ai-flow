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

import cloudpickle
from notification_service.event import EventKey, Event

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.internal.events import StartWorkflowExecutionEvent, StartTaskExecutionEvent
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
        with Workflow(name='workflow') as workflow:
            op = Operator(name='op')
            op.action_on_condition(action=TaskAction.START, condition=Condition(expect_events=[
                EventKey(namespace='namespace',
                         name='event_1',
                         event_type='event_type',
                         sender='sender'
                         ),
            ]))

        self.workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                                name=workflow.name,
                                                                content='',
                                                                workflow_object=cloudpickle.dumps(workflow))
        self.metadata_manager.flush()
        self.workflow_trigger \
            = self.metadata_manager.add_workflow_trigger(self.workflow_meta.id,
                                                         rule=cloudpickle.dumps(WorkflowRule(
                                                             condition=Condition(expect_events=[
                                                                 EventKey(namespace='namespace',
                                                                          name='event_2',
                                                                          event_type='event_type',
                                                                          sender='sender'
                                                                          ),
                                                             ]))))
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
        self.metadata_manager.update_workflow_execution_status(workflow_execution_id=self.workflow_execution_meta.id,
                                                               status=WorkflowStatus.RUNNING)
        self.metadata_manager.flush()

    def test_dispatch(self):
        worker_num = 3
        workers = []
        for i in range(worker_num):
            workers.append(Worker())
        dispatcher = Dispatcher(workers=workers, metadata_manager=self.metadata_manager)
        event: Event = StartWorkflowExecutionEvent(workflow_id=self.workflow_meta.id, snapshot_id=self.snapshot_meta.id)
        dispatcher.dispatch(event)
        self.assertEqual(1, workers[1].input_queue.qsize())

        event = StartTaskExecutionEvent(workflow_execution_id=2, task_name='op')
        dispatcher.dispatch(event)
        self.assertEqual(1, workers[2].input_queue.qsize())

        event = Event(event_key=EventKey(namespace='namespace',
                                         name='event_1',
                                         event_type='event_type',
                                         sender='sender'), message='')
        dispatcher.dispatch(event)
        self.assertEqual(2, workers[1].input_queue.qsize())

        event = Event(event_key=EventKey(namespace='namespace',
                                         name='event_2',
                                         event_type='event_type',
                                         sender='sender'), message='')
        dispatcher.dispatch(event)
        self.assertEqual(3, workers[1].input_queue.qsize())


if __name__ == '__main__':
    unittest.main()
