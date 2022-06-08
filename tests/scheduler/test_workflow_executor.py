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
from notification_service.event import EventKey

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.operator import Operator
from ai_flow.model.status import WorkflowStatus
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.schedule_command import WorkflowExecutionStartCommand, WorkflowExecutionStopCommand
from ai_flow.scheduler.workflow_executor import WorkflowExecutor
from tests.scheduler.test_utils import UnitTestWithNamespace


def build_workflow():
    expect_events_1 = [EventKey(namespace='namespace',
                                name='event_1',
                                event_type='event_type',
                                sender='sender'
                                )
                       ]
    expect_events_2 = [EventKey(namespace='namespace',
                                name='event_2',
                                event_type='event_type',
                                sender='sender'
                                )
                       ]

    with Workflow(name='workflow') as workflow:
        op_1 = Operator(name='op_1')
        op_2 = Operator(name='op_2')
        op_3 = Operator(name='op_3')
        op_4 = Operator(name='op_4')
        op_5 = Operator(name='op_5')

        op_1.action_on_condition(action=TaskAction.START,
                                 condition=Condition(expect_events=expect_events_1))
        op_2.action_on_condition(action=TaskAction.START,
                                 condition=Condition(expect_events=expect_events_2))
    return workflow


class TestWorkflowExecutor(UnitTestWithNamespace):

    def test_execute_workflow_command(self):
        workflow = build_workflow()
        workflow_meta = self.metadata_manager.add_workflow(namespace=self.namespace_name,
                                                           name=workflow.name,
                                                           content='',
                                                           workflow_object=cloudpickle.dumps(workflow))
        self.metadata_manager.session.flush()
        snapshot_meta = self.metadata_manager.add_workflow_snapshot(
            workflow_id=workflow_meta.id,
            workflow_object=workflow_meta.workflow_object,
            uri='url',
            signature='')
        self.metadata_manager.session.flush()

        workflow_executor = WorkflowExecutor(metadata_manager=self.metadata_manager)

        command = workflow_executor.execute(WorkflowExecutionStartCommand(snapshot_id=snapshot_meta.id))
        self.metadata_manager.commit()
        self.assertIsNotNone(command)
        self.assertEqual(3, len(command.task_schedule_commands))
        for c in command.task_schedule_commands:
            self.assertEqual(TaskAction.START, c.action)
            self.assertTrue(c.new_task_execution.task_name in {'op_3', 'op_4', 'op_5'})
            self.assertEqual(1, c.new_task_execution.seq_num)
        workflow_execution_meta = self.metadata_manager.get_workflow_execution(workflow_execution_id=1)
        self.assertEqual(WorkflowStatus.RUNNING.value, workflow_execution_meta.status)

        command = workflow_executor.execute(WorkflowExecutionStopCommand(workflow_execution_id=1))
        self.assertIsNotNone(command)
        self.assertEqual(3, len(command.task_schedule_commands))
        for tc in command.task_schedule_commands:
            self.assertEqual(TaskAction.STOP, tc.action)
        workflow_execution_meta = self.metadata_manager.get_workflow_execution(workflow_execution_id=1)
        self.assertEqual(WorkflowStatus.STOPPED.value, workflow_execution_meta.status)


if __name__ == '__main__':
    unittest.main()
