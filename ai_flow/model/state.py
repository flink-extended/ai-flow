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

class State(object):
    """User-defined state"""
    def clear(self):
        """Clean up user-defined state"""
        pass


class StateDescriptor(object):
    """User-defined state description"""
    def __init__(self, name):
        self.name = name


class StateType(object):
    VALUE = 'value'


class ValueState(State):
    """Single-valued user-defined state"""

    def value(self) -> object:
        """Get the single-valued user-defined state's value"""
        pass

    def update(self, state):
        """Update the single-valued user-defined state's value"""
        pass


class ValueStateDescriptor(StateDescriptor):
    """Single-valued user-defined state description"""
    pass
