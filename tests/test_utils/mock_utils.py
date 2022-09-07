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
from typing import List, Dict
from datetime import datetime
from notification_service.model.event import Event
from notification_service.client.notification_client import NotificationClient, \
    ListenerProcessor, ListenerRegistrationId

from ai_flow.scheduler.timer import Timer, build_trigger


class MockNotificationClient(NotificationClient):

    def __init__(self, server_uri=None, namespace=None, sender=None, **kwargs):
        self.events = []
        super().__init__(namespace, sender)

    def send_event(self, event: Event):
        event.namespace = self.namespace
        event.sender = self.sender
        self.events.append(event)
        return event

    def register_listener(self, listener_processor: ListenerProcessor, event_keys: List[str] = None,
                          offset: int = None) -> ListenerRegistrationId:
        pass

    def unregister_listener(self, registration_id: ListenerRegistrationId):
        pass

    def list_events(self, key: str = None, namespace: str = None, sender: str = None, begin_offset: int = None,
                    end_offset: int = None) -> List[Event]:
        return self.events

    def time_to_offset(self, time: datetime) -> int:
        pass

    def close(self):
        pass


class MockTimer(Timer):
    def __init__(self, notification_client=None, session=None):
        self.schedules: Dict = {}

    def start(self):
        pass

    def shutdown(self):
        pass

    def add_workflow_schedule_with_session(self, session, workflow_id, schedule_id,  expression):
        build_trigger(expression)
        self.schedules[schedule_id] = 'active'

    def delete_workflow_schedule_with_session(self, session, schedule_id):
        self.schedules.pop(schedule_id)

    def pause_workflow_schedule_with_session(self, session, schedule_id):
        self.schedules[schedule_id] = 'paused'

    def resume_workflow_schedule_with_session(self, session, schedule_id):
        self.schedules[schedule_id] = 'active'
