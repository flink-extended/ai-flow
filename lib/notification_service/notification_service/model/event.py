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
"""Definition of event."""
from typing import Optional


UNDEFINED_EVENT_TYPE = "UNDEFINED"
DEFAULT_NAMESPACE = "DEFAULT"
ANY_CONDITION = "*"


class EventKey(object):
    def __init__(self,
                 event_name: Optional[str],
                 event_type: Optional[str] = UNDEFINED_EVENT_TYPE):
        """
        EventKey represents a type of event.
        :param event_name: The event's name.
        :param event_type: The event's type.
        """
        self.event_name = event_name
        self.event_type = event_type

    def __str__(self) -> str:
        return 'event_name:{0}, event_type:{1}'.format(self.event_name, self.event_type)

    def __eq__(self, other):
        if not isinstance(other, EventKey):
            return False
        return self.event_name == other.event_name \
               and self.event_type == other.event_type


class Event(object):
    def __init__(self,
                 event_key: EventKey,
                 message: Optional[str],
                 ):
        """
        Event represents an event.
        :param event_key: It represents a type of event.
        :param message: It represents the event's message.
        """
        self.event_key = event_key
        self.message = message

        self._namespace = None
        self._sender = None
        self._create_time = None
        self._offset = None
        self._context = None

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value):
        self._namespace = value

    @property
    def sender(self):
        return self._sender

    @sender.setter
    def sender(self, value):
        self._sender = value

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, value):
        self._context = value

    @property
    def create_time(self):
        return self._create_time

    @create_time.setter
    def create_time(self, value):
        self._create_time = value

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value

    def __str__(self) -> str:
        return 'event_key:[{0}], message:{1}, namespace:{2}, sender:{3}, create_time:{4}, offset:{5}, context: {6}' \
            .format(self.event_key,
                    self.message,
                    self._namespace,
                    self._sender,
                    self._create_time,
                    self._offset,
                    self._context)

    def __eq__(self, other):
        if not isinstance(other, Event):
            return False
        return self.event_key == other.event_key \
               and self.message == other.message \
               and self._namespace == other.namespace \
               and self.sender == other.sender \
               and self._context == other.context \
               and self._create_time == other._create_time \
               and self._offset == other._offset
