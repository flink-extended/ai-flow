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
from typing import List
from datetime import datetime
from notification_service.event import Event, EventKey
from notification_service.notification_client import NotificationClient, ListenerProcessor, ListenerRegistrationId


class MockNotificationClient(NotificationClient):

    def __init__(self):
        super().__init__('namespace', 'sender')

    def send_event(self, event: Event):
        pass

    def register_listener(self, listener_processor: ListenerProcessor, event_keys: List[EventKey] = None,
                          offset: int = None) -> ListenerRegistrationId:
        pass

    def unregister_listener(self, id: ListenerRegistrationId):
        pass

    def list_events(self, name: str = None, namespace: str = None, event_type: str = None, sender: str = None,
                    offset: int = None) -> List[Event]:
        pass

    def time_to_offset(self, time: datetime) -> int:
        pass