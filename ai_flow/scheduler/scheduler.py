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

from ai_flow.common.util.db_util import session
from notification_service.event import Event
from notification_service.notification_client import NotificationClient, ListenerProcessor

from ai_flow.common.configuration import config_constants
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.scheduler.dispatcher import Dispatcher
from ai_flow.scheduler.worker import Worker
from ai_flow.task_executor.task_executor import TaskExecutor, TaskExecutorFactory


class Processor(ListenerProcessor):
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def process(self, events: List[Event]):
        for event in events:
            self.scheduler.trigger(event)


class EventDrivenScheduler(object):
    def __init__(self,
                 db_engine,
                 notification_client: NotificationClient,
                 schedule_worker_num: int = config_constants.SERVER_WORKER_NUMBER,
                 task_executor: TaskExecutor =
                 TaskExecutorFactory.get_task_executor(executor_type=config_constants.TASK_EXECUTOR)
                 ):
        self.db_engine = db_engine
        self.session = session.new_session(db_engine=self.db_engine)
        self.task_executor: TaskExecutor = task_executor
        self.notification_client = notification_client
        self.listener = None
        self.workers = []
        for i in range(schedule_worker_num):
            self.workers.append(Worker(max_queue_size=config_constants.SERVER_WORKER_QUEUE_SIZE,
                                       task_executor=self.task_executor,
                                       notification_client=self.notification_client))
        self.dispatcher = Dispatcher(workers=self.workers, metadata_manager=MetadataManager(session=self.session))

    def trigger(self, event: Event):
        self.dispatcher.dispatch(event=event)

    def get_last_committed_offset(self):
        metadata_manager = MetadataManager(self.session)

        return 0

    def start(self):
        self.task_executor.start()
        for i in range(len(self.workers)):
            self.workers[i].setDaemon(True)
            self.workers[i].setName('schedule_worker_{}'.format(i))
            self.workers[i].start()
        self.listener = self.notification_client.register_listener(
            listener_processor=Processor(self), offset=self.get_last_committed_offset())

    def stop(self):
        self.notification_client.unregister_listener(self.listener)
        self.session.close()
        session.Session.remove()
        self.task_executor.stop()
        for w in self.workers:
            w.stop()
