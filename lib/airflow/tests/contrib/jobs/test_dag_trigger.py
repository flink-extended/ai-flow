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
import multiprocessing
import os
import time
import unittest

import pendulum.datetime
from notification_service.base_notification import BaseEvent
from notification_service.client import NotificationClient
from notification_service.event_storage import MemoryEventStorage
from notification_service.server import NotificationServer
from notification_service.service import NotificationService
from airflow.models.serialized_dag import SerializedDagModel

from airflow.contrib.jobs.dag_trigger import DagTrigger
from airflow.contrib.jobs.scheduler_client import EventSchedulerClient, ResponseWatcher
from airflow.models import DagModel
from airflow.utils.mailbox import Mailbox
from airflow.utils.session import create_session
from airflow.events.scheduler_events import SchedulerInnerEventUtil, SchedulerInnerEventType, SCHEDULER_NAMESPACE
from tests.test_utils import db
from tests.test_utils.config import conf_vars

DAG_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dags')
TEST_DAG_FILE = os.path.join(DAG_FOLDER, 'test_scheduler_dags.py')


class TestDagTrigger(unittest.TestCase):

    def setUp(self) -> None:
        db.clear_db_dags()
        db.clear_db_serialized_dags()

    def test_dag_trigger_is_alive(self):
        mailbox = Mailbox()
        dag_trigger = DagTrigger(".", -1, [], False, mailbox)
        assert not dag_trigger.is_alive()
        dag_trigger.start()
        time.sleep(1)
        assert dag_trigger.is_alive()
        dag_trigger.end()
        assert not dag_trigger.is_alive()

    def test_dag_trigger(self):
        mailbox = Mailbox()
        dag_trigger = DagTrigger(".", -1, [], False, mailbox)
        dag_trigger.start()
        type(self)._add_dag_needing_dagrun()

        message = mailbox.get_message()
        message = SchedulerInnerEventUtil.to_inner_event(message)
        assert message.dag_id == "test"
        dag_trigger.end()

    def test_dag_trigger_parse_dag(self):
        mailbox = Mailbox()
        dag_trigger = DagTrigger(TEST_DAG_FILE, -1, [], False, mailbox)
        dag_trigger.start()

        message = mailbox.get_message()
        message = SchedulerInnerEventUtil.to_inner_event(message)
        # only one dag is executable
        assert "test_task_start_date_scheduling" == message.dag_id

        assert DagModel.get_dagmodel(dag_id="test_task_start_date_scheduling") is not None
        assert DagModel.get_dagmodel(dag_id="test_start_date_scheduling") is not None
        assert SerializedDagModel.get(dag_id="test_task_start_date_scheduling") is not None
        assert SerializedDagModel.get(dag_id="test_start_date_scheduling") is not None
        dag_trigger.end()

    def test_user_trigger_parse_dag(self):
        port = 50101
        notification_server_uri = 'localhost:{}'.format(port)
        storage = MemoryEventStorage()
        server = NotificationServer(NotificationService(storage), port)
        server.run()
        mailbox = Mailbox()
        dag_trigger = DagTrigger(TEST_DAG_FILE, -1, [], False, mailbox, 5, notification_server_uri)
        dag_trigger.start()
        message = mailbox.get_message()
        message = SchedulerInnerEventUtil.to_inner_event(message)
        # only one dag is executable
        assert "test_task_start_date_scheduling" == message.dag_id
        sc = EventSchedulerClient(notification_server_uri=notification_server_uri, namespace='a')
        sc.trigger_parse_dag(TEST_DAG_FILE)
        dag_trigger.end()
        server.stop()

    @unittest.skip("possibly blocked")
    def test_file_processor_manager_kill(self):
        mailbox = Mailbox()
        dag_trigger = DagTrigger(".", -1, [], False, mailbox)
        dag_trigger.start()
        dag_file_processor_manager_process = dag_trigger._dag_file_processor_agent._process
        dag_file_processor_manager_process.kill()
        dag_file_processor_manager_process.join(1)
        assert not dag_file_processor_manager_process.is_alive()
        cnt = 0
        while cnt < 100 and not dag_file_processor_manager_process.is_alive():
            dag_file_processor_manager_process = dag_trigger._dag_file_processor_agent._process
            if not dag_file_processor_manager_process.is_alive():
                time.sleep(0.1)
                cnt = cnt + 1
                continue
            else:
                break
        assert dag_file_processor_manager_process.is_alive()
        dag_trigger.end()

    def _send_request_and_receive_response(self, notification_server_uri, file_path):
        key = '{}_{}'.format(file_path, time.time_ns())
        client = NotificationClient(server_uri=notification_server_uri,
                                    default_namespace=SCHEDULER_NAMESPACE)
        event = BaseEvent(key=key,
                          event_type=SchedulerInnerEventType.PARSE_DAG_REQUEST.value,
                          value=file_path)
        watcher: ResponseWatcher = ResponseWatcher()
        client.start_listen_event(key=key,
                                  event_type=SchedulerInnerEventType.PARSE_DAG_RESPONSE.value,
                                  watcher=watcher)
        client.send_event(event)
        res: BaseEvent = watcher.get_result()
        self.assertEquals(event.key, res.key)
        self.assertEquals(event.value, file_path)
        client.stop_listen_events()

    @staticmethod
    def _add_dag_needing_dagrun():
        with create_session() as session:
            orm_dag = DagModel(dag_id="test")
            orm_dag.is_paused = False
            orm_dag.is_active = True
            orm_dag.next_dagrun_create_after = pendulum.now()
            session.merge(orm_dag)
            session.commit()


if __name__ == '__main__':
    unittest.main()
