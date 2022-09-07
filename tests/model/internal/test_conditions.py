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

from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.internal.conditions import SingleEventCondition, MeetAllCondition, MeetAnyCondition
from ai_flow.model.state import StateDescriptor, State, ValueState
from ai_flow.model.status import TaskStatus


class MockCondition(Condition):
    def __init__(self, name: str, flag: bool):
        super().__init__([name])
        self.flag = flag

    def is_met(self, event: Event, context: Context) -> bool:
        return self.flag


class MockCondition2(Condition):
    def __init__(self, name: str):
        super().__init__([name])
        self.count = 0

    def is_met(self, event: Event, context: Context) -> bool:
        self.count += 1
        if 1 == self.count % 2:
            return True
        else:
            return False


class MockValueState(ValueState):
    def __init__(self):
        self.obj = None

    def clear(self):
        self.obj = None

    def value(self) -> object:
        return self.obj

    def update(self, state):
        self.obj = state


class MockContext(Context):
    state = MockValueState()

    def clear(self):
        self.state.clear()

    def get_state(self, state_descriptor: StateDescriptor) -> State:
        return self.state

    def get_task_status(self, task_name) -> TaskStatus:
        return super().get_task_status(task_name)


class TestConditions(unittest.TestCase):

    def test_single_event_condition(self):
        self.assertEqual(True, SingleEventCondition(expect_event_key='a').is_met(event=None, context=None))

    def test_meet_any_condition(self):
        c_1 = MockCondition(name='1', flag=True)
        c_2 = MockCondition(name='2', flag=False)
        any_condition_1 = MeetAnyCondition(conditions=[c_1, c_1])
        self.assertTrue(any_condition_1.is_met(
            event=Event(key='1', value=None), context=None))

        any_condition_2 = MeetAnyCondition(conditions=[c_2, c_2])
        self.assertFalse(any_condition_2.is_met(
            event=Event(key='2', value=None), context=None))

        any_condition_3 = MeetAnyCondition(conditions=[c_1, c_2])
        self.assertTrue(any_condition_3.is_met(
            event=Event(key='1', value=None), context=None))
        self.assertFalse(any_condition_3.is_met(
            event=Event(key='2', value=None), context=None))

    def test_meet_all_condition(self):
        context = MockContext()
        c_1 = MockCondition(name='1', flag=True)
        c_2 = MockCondition(name='2', flag=True)
        condition = MeetAllCondition(name='c', conditions=[c_1, c_2])
        self.assertFalse(condition.is_met(
            event=Event(key='1', value=None), context=context))
        self.assertTrue(condition.is_met(
            event=Event(key='2', value=None), context=context))
        context.clear()
        c_3 = MockCondition2(name='1')
        condition = MeetAllCondition(name='c', conditions=[c_2, c_3])
        self.assertFalse(condition.is_met(
            event=Event(key='2', value=None), context=context))
        self.assertTrue(condition.is_met(
            event=Event(key='1', value=None), context=context))
        self.assertFalse(condition.is_met(
            event=Event(key='1', value=None), context=context))


if __name__ == '__main__':
    unittest.main()
