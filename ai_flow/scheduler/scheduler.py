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
from notification_service.event import Event
from ai_flow.common.configuration import config_constants
from ai_flow.common.util.db_util.session import new_session, create_sqlalchemy_engine, prepare_session
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.scheduler.dispatcher import Dispatcher
from ai_flow.scheduler.worker import Worker
from ai_flow.task_executor.task_executor import TaskExecutor, TaskExecutorFactory


class EventDrivenScheduler(object):
    def __init__(self,
                 db_engine,
                 schedule_worker_num: int = config_constants.SERVER_WORKER_NUMBER,
                 task_executor: TaskExecutor =
                 TaskExecutorFactory.get_task_executor(executor_type=config_constants.TASK_EXECUTOR)
                 ):
        self.db_engine = db_engine
        self.session = new_session(db_engine=self.db_engine)
        self.task_executor: TaskExecutor = task_executor
        self.workers = []
        for i in range(schedule_worker_num):
            self.workers.append(Worker(max_queue_size=config_constants.SERVER_WORKER_QUEUE_SIZE,
                                       task_executor=self.task_executor))
        self.dispatcher = Dispatcher(workers=self.workers, metadata_manager=MetadataManager(session=self.session))

    def trigger(self, event: Event):
        self.dispatcher.dispatch(event=event)

    def start(self):
        self.task_executor.start()
        for i in range(len(self.workers)):
            self.workers[i].setDaemon(True)
            self.workers[i].setName('schedule_worker_{}'.format(i))
            self.workers[i].start()

    def stop(self):
        self.session.close()
        self.task_executor.stop()
        for w in self.workers:
            w.stop()
