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
import unittest

import cloudpickle
from notification_service.model.event import Event

from ai_flow.model.action import TaskAction
from ai_flow.model.internal.events import StartWorkflowExecutionEvent, StopTaskExecutionEvent, StartTaskExecutionEvent, \
    ReStartTaskExecutionEvent, PeriodicRunWorkflowEvent, PeriodicRunTaskEvent, StopWorkflowExecutionEvent, \
    TaskStatusEvent, TaskHeartbeatTimeoutEvent
from ai_flow.model.operator import Operator
from ai_flow.model.status import TaskStatus, WorkflowStatus
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.scheduling_event_processor import SchedulingEventProcessor
from ai_flow.scheduler.schedule_command import WorkflowExecutionStartCommand, WorkflowExecutionStopCommand, \
    WorkflowExecutionScheduleCommand
from ai_flow.scheduler.workflow_executor import WorkflowExecutor
from tests.scheduler.test_utils import UnitTestWithNamespace


class TestSchedulingEventProcessor(UnitTestWithNamespace):
    def setUp(self) -> None:
        super().setUp()
        with Workflow(name='workflow') as workflow:
            task1 = Operator(name='task1')
            task2 = Operator(name='task2')
            task2.action_on_task_status(TaskAction.START, {task1: TaskStatus.SUCCESS})

        self.workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                                name=workflow.name,
                                                                content='',
                                                                workflow_object=cloudpickle.dumps(workflow))
        self.metadata_manager.flush()
        self.snapshot_meta = self.metadata_manager.add_workflow_snapshot(
            workflow_id=self.workflow_meta.id,
            workflow_object=self.workflow_meta.workflow_object,
            uri='url',
            signature='')
        self.metadata_manager.flush()

    def test_start_stop_event(self):
        scheduling_event_processor = SchedulingEventProcessor(metadata_manager=self.metadata_manager)
        workflow_executor = WorkflowExecutor(metadata_manager=self.metadata_manager)
        event: Event = StartWorkflowExecutionEvent(workflow_id=self.workflow_meta.id, snapshot_id=self.snapshot_meta.id)
        command = scheduling_event_processor.process(event)
        self.assertTrue(isinstance(command, WorkflowExecutionStartCommand))
        self.assertEquals(self.snapshot_meta.id, command.snapshot_id)
        command = workflow_executor.execute(command)
        workflow_execution_id = command.workflow_execution_id
        self.assertTrue(isinstance(command, WorkflowExecutionScheduleCommand))
        self.assertEqual(1, len(command.task_schedule_commands))
        self.assertEqual(TaskAction.START, command.task_schedule_commands[0].action)
        task_metas = self.metadata_manager.list_task_executions(workflow_execution_id=workflow_execution_id,
                                                                page_size=None)
        self.assertEqual(1, len(task_metas))

        event = StartTaskExecutionEvent(workflow_execution_id=workflow_execution_id, task_name='task1')
        command = scheduling_event_processor.process(event)
        self.assertIsNone(command)

        event = ReStartTaskExecutionEvent(workflow_execution_id=workflow_execution_id, task_name='task1')
        command = scheduling_event_processor.process(event)
        self.assertTrue(isinstance(command, WorkflowExecutionScheduleCommand))
        self.assertEqual(1, len(command.task_schedule_commands))
        self.assertEqual(TaskAction.RESTART, command.task_schedule_commands[0].action)
        task_metas = self.metadata_manager.list_task_executions(workflow_execution_id=command.workflow_execution_id,
                                                                page_size=None)
        self.assertEqual(2, len(task_metas))

        event = StopTaskExecutionEvent(workflow_execution_id=task_metas[1].workflow_execution_id,
                                       task_execution_id=task_metas[1].id)
        command = scheduling_event_processor.process(event)
        self.assertTrue(isinstance(command, WorkflowExecutionScheduleCommand))
        self.assertEqual(1, len(command.task_schedule_commands))
        self.assertEqual(TaskAction.STOP, command.task_schedule_commands[0].action)

        event = StopWorkflowExecutionEvent(workflow_execution_id=command.workflow_execution_id)
        command = scheduling_event_processor.process(event)
        self.assertTrue(isinstance(command, WorkflowExecutionStopCommand))
        command = workflow_executor.execute(command)
        self.assertTrue(isinstance(command, WorkflowExecutionScheduleCommand))
        self.assertEqual(TaskAction.STOP, command.task_schedule_commands[0].action)

    def test_periodic_event(self):
        scheduling_event_processor = SchedulingEventProcessor(metadata_manager=self.metadata_manager)
        workflow_executor = WorkflowExecutor(metadata_manager=self.metadata_manager)

        schedule_meta = self.metadata_manager.add_workflow_schedule(workflow_id=self.workflow_meta.id,
                                                                    expression='interval@0 0 0 1')
        self.metadata_manager.flush()
        event = PeriodicRunWorkflowEvent(workflow_id=schedule_meta.workflow_id,
                                         schedule_id=schedule_meta.id)
        command = scheduling_event_processor.process(event)
        self.assertTrue(isinstance(command, WorkflowExecutionStartCommand))
        self.assertEquals(self.snapshot_meta.id, command.snapshot_id)
        command = workflow_executor.execute(command)
        workflow_execution_id = command.workflow_execution_id
        self.assertTrue(isinstance(command, WorkflowExecutionScheduleCommand))
        self.assertEqual(1, len(command.task_schedule_commands))
        self.assertEqual(TaskAction.START, command.task_schedule_commands[0].action)

        event = PeriodicRunTaskEvent(workflow_execution_id=workflow_execution_id, task_name='task1')
        command = scheduling_event_processor.process(event)
        self.metadata_manager.flush()
        self.assertTrue(isinstance(command, WorkflowExecutionScheduleCommand))
        self.assertEqual(1, len(command.task_schedule_commands))
        self.assertEqual(TaskAction.RESTART, command.task_schedule_commands[0].action)

    def test_task_timeout_event(self):
        scheduling_event_processor = SchedulingEventProcessor(metadata_manager=self.metadata_manager)
        workflow_executor = WorkflowExecutor(metadata_manager=self.metadata_manager)
        event: Event = StartWorkflowExecutionEvent(workflow_id=self.workflow_meta.id, snapshot_id=self.snapshot_meta.id)
        command = scheduling_event_processor.process(event)
        command = workflow_executor.execute(command)
        self.metadata_manager.flush()
        workflow_execution_id = command.workflow_execution_id
        seq_num = command.task_schedule_commands[0].new_task_execution.seq_num
        event = TaskStatusEvent(workflow_execution_id=workflow_execution_id,
                                task_name='task1',
                                sequence_number=seq_num,
                                status=TaskStatus.RUNNING)
        command = scheduling_event_processor.process(event)
        self.metadata_manager.flush()
        self.assertIsNone(command)
        task_meta = self.metadata_manager.get_task_execution(workflow_execution_id=workflow_execution_id,
                                                             task_name='task1',
                                                             sequence_number=seq_num)
        self.assertEqual(TaskStatus.RUNNING, TaskStatus(task_meta.status))

        event = TaskHeartbeatTimeoutEvent(workflow_execution_id=workflow_execution_id,
                                          task_name='task1',
                                          sequence_number=seq_num)
        command = scheduling_event_processor.process(event)
        self.metadata_manager.flush()
        self.assertIsNone(command)
        task_meta = self.metadata_manager.get_task_execution(workflow_execution_id=workflow_execution_id,
                                                             task_name='task1',
                                                             sequence_number=seq_num)
        self.assertEqual(TaskStatus.FAILED, TaskStatus(task_meta.status))

        workflow_execution_meta = self.metadata_manager.get_workflow_execution(
            workflow_execution_id=workflow_execution_id)
        self.assertEqual(WorkflowStatus.RUNNING, WorkflowStatus(workflow_execution_meta.status))

    def test_task_success_event(self):
        scheduling_event_processor = SchedulingEventProcessor(metadata_manager=self.metadata_manager)
        workflow_executor = WorkflowExecutor(metadata_manager=self.metadata_manager)
        event: Event = StartWorkflowExecutionEvent(workflow_id=self.workflow_meta.id, snapshot_id=self.snapshot_meta.id)
        command = scheduling_event_processor.process(event)
        command = workflow_executor.execute(command)
        self.metadata_manager.flush()
        workflow_execution_id = command.workflow_execution_id
        self.metadata_manager.add_task_execution(workflow_execution_id, 'task2')
        seq_num = command.task_schedule_commands[0].new_task_execution.seq_num
        event = TaskStatusEvent(workflow_execution_id=workflow_execution_id,
                                task_name='task1',
                                sequence_number=seq_num,
                                status=TaskStatus.SUCCESS)
        event2 = TaskStatusEvent(workflow_execution_id=workflow_execution_id,
                                 task_name='task2',
                                 sequence_number=seq_num,
                                 status=TaskStatus.SUCCESS)
        command = scheduling_event_processor.process(event)
        scheduling_event_processor.process(event2)
        workflow_execution_meta = self.metadata_manager.get_workflow_execution(
            workflow_execution_id=workflow_execution_id)
        self.assertEqual(WorkflowStatus.SUCCESS, WorkflowStatus(workflow_execution_meta.status))


if __name__ == '__main__':
    unittest.main()
