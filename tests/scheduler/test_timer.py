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
import os
import time
import unittest
from datetime import datetime
from typing import List

from notification_service.event import Event, EventKey
from notification_service.notification_client import NotificationClient, ListenerRegistrationId, ListenerProcessor

from ai_flow.common.util.db_migration import init_db
from ai_flow.common.util.db_util.session import new_session
from ai_flow.model.internal.events import PeriodicRunWorkflowEvent, PeriodicRunTaskEvent
from ai_flow.scheduler.timer import Timer


results = []


class MockNotificationClient(NotificationClient):

    def __init__(self):
        super().__init__('namespace', 'sender')

    def send_event(self, event: Event):
        global results
        results.append(event)

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


class TestTimer(unittest.TestCase):
    def setUp(self) -> None:
        self.file = 'test.db'
        self._delete_db_file()
        self.url = 'sqlite:///{}'.format(self.file)
        init_db(self.url)
        self.session = new_session(db_uri=self.url)
        self.notification_client = MockNotificationClient()

    def _delete_db_file(self):
        if os.path.exists(self.file):
            os.remove(self.file)

    def tearDown(self) -> None:
        global results
        self.session.close()
        self._delete_db_file()
        results.clear()

    def test_workflow_schedule_cron_expression(self):
        global results
        timer = Timer(notification_client=self.notification_client, session=self.session)
        timer.start()

        timer.add_workflow_schedule(schedule_id=1,
                                    expression='cron@*/1 * * * * * * utc')
        self.session.commit()
        jobs = timer.store.get_all_jobs()
        self.assertEqual(1, len(jobs))
        timer.pause_workflow_schedule(schedule_id=1)
        time.sleep(2)
        self.assertEqual(0, len(results))
        timer.resume_workflow_schedule(schedule_id=1)
        time.sleep(2)
        self.assertEqual(2, len(results))
        self.assertTrue(isinstance(results[0], PeriodicRunWorkflowEvent))
        timer.delete_workflow_schedule(1)
        jobs = timer.store.get_all_jobs()
        self.assertEqual(0, len(jobs))
        timer.shutdown()

    def test_workflow_schedule_interval_expression(self):
        global results
        timer = Timer(notification_client=self.notification_client, session=self.session)
        timer.start()

        timer.add_workflow_schedule(schedule_id=1,
                                    expression='interval@0 0 0 1')
        jobs = timer.store.get_all_jobs()
        self.assertEqual(1, len(jobs))
        time.sleep(2.5)
        self.assertEqual(2, len(results))
        self.assertTrue(isinstance(results[0], PeriodicRunWorkflowEvent))
        timer.delete_workflow_schedule(1)
        jobs = timer.store.get_all_jobs()
        self.assertEqual(0, len(jobs))
        timer.shutdown()

    def test_task_schedule_cron_expression(self):
        global results
        timer = Timer(notification_client=self.notification_client, session=self.session)
        timer.start()

        timer.add_task_schedule(workflow_execution_id=1,
                                task_name='task',
                                expression='cron@*/1 * * * * * * utc')
        jobs = timer.store.get_all_jobs()
        self.assertEqual(1, len(jobs))
        time.sleep(2)
        self.assertEqual(2, len(results))
        self.assertTrue(isinstance(results[0], PeriodicRunTaskEvent))
        timer.delete_task_schedule(workflow_execution_id=1, task_name='task')
        jobs = timer.store.get_all_jobs()
        self.assertEqual(0, len(jobs))
        timer.shutdown()

    def test_task_schedule_interval_expression(self):
        global results
        timer = Timer(notification_client=self.notification_client, session=self.session)
        timer.start()

        timer.add_task_schedule(workflow_execution_id=1,
                                task_name='task',
                                expression='interval@0 0 0 1')
        jobs = timer.store.get_all_jobs()
        self.assertEqual(1, len(jobs))
        time.sleep(2.5)
        self.assertEqual(2, len(results))
        self.assertTrue(isinstance(results[0], PeriodicRunTaskEvent))
        timer.delete_task_schedule(workflow_execution_id=1, task_name='task')
        jobs = timer.store.get_all_jobs()
        self.assertEqual(0, len(jobs))
        timer.shutdown()


if __name__ == '__main__':
    unittest.main()
