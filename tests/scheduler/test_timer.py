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
import threading
import unittest
from datetime import datetime
from typing import List

from notification_service.model.event import Event
from notification_service.client.notification_client import NotificationClient, ListenerRegistrationId, ListenerProcessor
from tests.test_utils.unittest_base import BaseUnitTest

from ai_flow.common.util.db_util.session import create_session
from ai_flow.scheduler.timer import Timer


class TestTimer(BaseUnitTest):
    def setUp(self) -> None:
        super().setUp()

    def test_workflow_schedule_cron_expression(self):
        timer = Timer()
        timer.start()

        timer.add_workflow_schedule(workflow_id=None,
                                    schedule_id=1,
                                    expression='cron@*/1 * * * *')
        self.session.commit()
        jobs = timer.store.get_all_jobs()
        self.assertEqual(1, len(jobs))
        timer.pause_workflow_schedule(schedule_id=1)
        self.session.commit()
        self.assertEqual(None, timer.store.lookup_job(jobs[0].id).next_run_time)
        timer.resume_workflow_schedule(schedule_id=1)
        self.session.commit()
        self.assertIsNotNone(timer.store.lookup_job(jobs[0].id).next_run_time)
        timer.delete_workflow_schedule(1)
        jobs = timer.store.get_all_jobs()
        self.assertEqual(0, len(jobs))
        timer.shutdown()

    def test_workflow_schedule_interval_expression(self):
        timer = Timer()
        timer.start()

        timer.add_workflow_schedule(workflow_id=None,
                                    schedule_id=1,
                                    expression='interval@0 0 0 1')
        self.session.commit()
        jobs = timer.store.get_all_jobs()
        self.assertEqual(1, len(jobs))
        self.assertIsNotNone(timer.store.lookup_job(jobs[0].id).next_run_time)
        timer.delete_workflow_schedule(1)
        jobs = timer.store.get_all_jobs()
        self.assertEqual(0, len(jobs))
        timer.shutdown()

    def test_task_schedule_cron_expression(self):
        timer = Timer()
        timer.start()

        timer.add_task_schedule(workflow_execution_id=1,
                                task_name='task',
                                expression='cron@*/1 * * * *')
        self.session.commit()
        jobs = timer.store.get_all_jobs()
        self.assertEqual(1, len(jobs))
        self.assertIsNotNone(timer.store.lookup_job(jobs[0].id).next_run_time)
        timer.delete_task_schedule(workflow_execution_id=1, task_name='task')
        jobs = timer.store.get_all_jobs()
        self.assertEqual(0, len(jobs))
        timer.shutdown()

    def test_task_schedule_interval_expression(self):
        timer = Timer()
        timer.start()

        timer.add_task_schedule(workflow_execution_id=1,
                                task_name='task',
                                expression='interval@0 0 0 1')
        self.session.commit()
        jobs = timer.store.get_all_jobs()
        self.assertEqual(1, len(jobs))
        self.assertIsNotNone(timer.store.lookup_job(jobs[0].id).next_run_time)
        timer.delete_task_schedule(workflow_execution_id=1, task_name='task')
        jobs = timer.store.get_all_jobs()
        self.assertEqual(0, len(jobs))
        timer.shutdown()

    def test_update_schedule_in_multi_threads(self):
        timer = Timer()
        timer.start()
        timer.add_task_schedule(workflow_execution_id=1,
                                task_name='task1',
                                expression='interval@0 0 2 0')
        jobs = timer.store.get_all_jobs()
        self.assertEqual(1, len(jobs))

        def update_schedule(seed):
            for i in range(100):
                with create_session() as session:
                    timer.add_task_schedule_with_session(
                        session, i+seed, 'task2', 'interval@0 0 1 0')
        t1 = threading.Thread(target=update_schedule, args=(0,))
        t1.start()
        t2 = threading.Thread(target=update_schedule, args=(1000,))
        t2.start()
        t1.join()
        t2.join()
        jobs = timer.store.get_all_jobs()
        self.assertEqual(201, len(jobs))
        timer.shutdown()



if __name__ == '__main__':
    unittest.main()
