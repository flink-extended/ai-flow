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
import time
import unittest

import cloudpickle
from notification_service.model.event import Event

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.internal.events import StartWorkflowExecutionEvent, StopTaskExecutionEvent
from ai_flow.model.operator import Operator
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.status import TaskStatus
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.schedule_command import TaskScheduleCommand
from ai_flow.scheduler.scheduler import EventDrivenScheduler
from ai_flow.task_executor.task_executor import TaskExecutor
from tests.scheduler.test_utils import UnitTestWithNamespace


class MockTaskExecutor(TaskExecutor):
    def schedule_task(self, command: TaskScheduleCommand):
        self.commands.append(command)

    def __init__(self):
        self.commands = []

    def start(self):
        pass

    def stop(self):
        pass


class TrueCondition(Condition):
    def is_met(self, event: Event, context: Context) -> bool:
        return True


def wait_scheduler_done(scheduler: EventDrivenScheduler):
    flag = True
    while flag:
        for worker in scheduler.workers:
            if worker.input_queue.unfinished_tasks > 0:
                flag = False
                break
        time.sleep(0.1)


class TestEventDrivenScheduler(UnitTestWithNamespace):
    def setUp(self) -> None:
        super().setUp()
        with Workflow(name='workflow', namespace=self.namespace_name) as workflow:
            op1 = Operator(name='op_1')
            op2 = Operator(name='op_2')
            op1.action_on_condition(action=TaskAction.START,
                                    condition=TrueCondition(expect_event_keys=['event_1']))

        self.workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                                name=workflow.name,
                                                                content='',
                                                                workflow_object=cloudpickle.dumps(workflow))
        self.metadata_manager.flush()
        self.workflow_trigger = self.metadata_manager.add_workflow_trigger(
            workflow_id=self.workflow_meta.id,
            rule=cloudpickle.dumps(
                WorkflowRule(
                    condition=TrueCondition(expect_event_keys=['event_2'])
                )
            )
        )
        self.metadata_manager.flush()
        self.snapshot_meta = self.metadata_manager.add_workflow_snapshot(
            workflow_id=self.workflow_meta.id,
            workflow_object=self.workflow_meta.workflow_object,
            uri='url',
            signature='')
        self.metadata_manager.commit()

    def test_scheduler_run(self):
        task_executor = MockTaskExecutor()
        scheduler = EventDrivenScheduler(task_executor=task_executor, schedule_worker_num=3)
        try:
            scheduler.start()
            event: Event = StartWorkflowExecutionEvent(workflow_id=self.workflow_meta.id,
                                                       snapshot_id=self.snapshot_meta.id)
            event.namespace = self.namespace_name
            event.offset = 1
            scheduler.trigger(event)
            wait_scheduler_done(scheduler)
            self.assertEqual(1, len(task_executor.commands))
            self.assertTrue(isinstance(task_executor.commands[0], TaskScheduleCommand))
            self.assertEqual(TaskAction.START, task_executor.commands[0].action)
            wes = self.metadata_manager.list_workflow_executions(workflow_id=self.workflow_meta.id)
            self.assertEqual(1, len(wes))
            tes = self.metadata_manager.list_task_executions(workflow_execution_id=wes[0].id)
            self.assertEqual(1, len(tes))
            self.assertEqual(TaskStatus.QUEUED, tes[0].status)
            self.assertEqual('op_2', tes[0].task_name)
            offset = self.metadata_manager.get_workflow_event_offset(workflow_id=self.workflow_meta.id)
            self.assertEqual(1, offset)

            event = Event(key='event_1', value='')
            event.offset = 2
            event.namespace = self.namespace_name
            scheduler.trigger(event)
            wait_scheduler_done(scheduler)

            self.assertEqual(2, len(task_executor.commands))
            te = self.metadata_manager.get_task_execution(workflow_execution_id=wes[0].id,
                                                          task_name='op_1',
                                                          sequence_number=1)
            self.assertEqual(TaskStatus.QUEUED, te.status)

            event = StopTaskExecutionEvent(workflow_execution_id=te.workflow_execution_id, task_execution_id=te.id)
            event.offset = 3
            event.namespace = self.namespace_name
            scheduler.trigger(event)
            wait_scheduler_done(scheduler)
            self.assertEqual(3, len(task_executor.commands))
            self.metadata_manager.session.refresh(te)
            self.assertEqual(TaskStatus.STOPPING, te.status)

            event = Event(key='event_2', value='')
            event.offset = 4
            event.namespace = self.namespace_name
            scheduler.trigger(event)
            wait_scheduler_done(scheduler)
            self.assertEqual(4, len(task_executor.commands))
            wes = self.metadata_manager.list_workflow_executions(workflow_id=self.workflow_meta.id)
            self.assertEqual(2, len(wes))
            tes = self.metadata_manager.list_task_executions(workflow_execution_id=wes[1].id)
            self.assertEqual(1, len(tes))
        finally:
            scheduler.stop()


if __name__ == '__main__':
    unittest.main()
