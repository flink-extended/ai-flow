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
from notification_service.base_notification import BaseEvent
from ai_flow.client.notification_client import get_notification_client
from ai_flow.context.project_context import set_current_project_config
from ai_flow.context.job_context import set_current_job_name, unset_current_job_name
from ai_flow.test.util.notification_service_utils import start_notification_server, stop_notification_server, _NS_URI


class TestNotificationClient(unittest.TestCase):

    def setUp(self) -> None:
        self.ns_server = start_notification_server()

    def tearDown(self) -> None:
        stop_notification_server(self.ns_server)

    def test_get_notification_client(self):
        config = {'notification_server_uri': _NS_URI, 'project_name': 'test_project'}
        set_current_project_config(config)
        set_current_job_name('job_1')
        client = get_notification_client()
        client.send_event(BaseEvent(key='a', value='a'))
        events = client.list_all_events(start_version=0)
        self.assertEqual(1, len(events))
        self.assertEqual('test_project', events[0].namespace)
        self.assertEqual('job_1', events[0].sender)
        self.assertEqual('a', events[0].key)
        self.assertEqual('a', events[0].value)
        unset_current_job_name()


if __name__ == '__main__':
    unittest.main()
