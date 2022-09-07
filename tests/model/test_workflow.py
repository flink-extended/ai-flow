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

from notification_service.model.event import Event

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.operator import Operator
from ai_flow.model.status import TaskStatus
from ai_flow.model.workflow import Workflow


class MockOperator(Operator):
    pass


class MockCondition(Condition):
    def __init__(self):
        super().__init__([])

    def is_met(self, event: Event, context: Context) -> bool:
        pass


class TestWorkflow(unittest.TestCase):

    def test_action_on_condition(self):

        with Workflow(name='workflow') as workflow:
            task_1 = MockOperator(name='task_1')
            task_2 = MockOperator(name='task_2')
            task_1.action_on_condition(TaskAction.START, MockCondition())
            task_1.action_on_condition(TaskAction.START, MockCondition())
            task_2.action_on_condition(TaskAction.START, MockCondition())
        self.assertEqual(2, len(workflow.tasks))
        self.assertEqual(2, len(workflow.rules['task_1']))
        self.assertEqual(1, len(workflow.rules['task_2']))

    def test_action_on_event_received(self):

        with Workflow(name='workflow') as workflow:
            task = MockOperator(name='task')
            task.action_on_event_received(event_key='a', action=TaskAction.START)
            task.action_on_event_received(event_key='b', action=TaskAction.STOP)
        self.assertEqual(1, len(workflow.tasks))
        self.assertEqual(2, len(workflow.rules['task']))
        self.assertEqual(TaskAction.START, workflow.rules['task'][0].action)
        self.assertEqual(TaskAction.STOP, workflow.rules['task'][1].action)

    def test_action_on_task_status(self):
        with Workflow(name='workflow') as workflow:
            task_1 = MockOperator(name='task_1')
            task_2 = MockOperator(name='task_2')
            task_3 = MockOperator(name='task_3')
            task_3.action_on_task_status(action=TaskAction.START,
                                         upstream_task_status_dict={task_1: TaskStatus.SUCCESS,
                                                                    task_2: TaskStatus.FAILED})
        self.assertEqual(3, len(workflow.tasks))
        self.assertEqual(1, len(workflow.rules['task_3']))
        self.assertEqual(2, len(workflow.rules['task_3'][0].condition.condition_list))


if __name__ == '__main__':
    unittest.main()
