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
import sys

from notification_service.model.event import Event

from ai_flow.common.configuration import config_constants
from ai_flow.scheduler.dispatcher import Dispatcher
from ai_flow.scheduler.worker import Worker
from ai_flow.task_executor.task_executor import TaskExecutor, TaskExecutorFactory


class EventDrivenScheduler(object):
    def __init__(self,
                 schedule_worker_num: int = config_constants.SERVER_WORKER_NUMBER,
                 task_executor: TaskExecutor = None,
                 ):
        self.task_executor = task_executor if task_executor is not None else \
            TaskExecutorFactory.get_task_executor(executor_type=config_constants.TASK_EXECUTOR)
        self.workers = []
        for i in range(schedule_worker_num):
            self.workers.append(Worker(max_queue_size=config_constants.SERVER_WORKER_QUEUE_SIZE,
                                       task_executor=self.task_executor))
        self.dispatcher = Dispatcher(workers=self.workers)

    def trigger(self, event: Event):
        self.dispatcher.dispatch(event=event)

    def get_minimum_committed_offset(self):
        result = sys.maxsize
        for i in range(len(self.workers)):
            offset = self.workers[i].last_committed_offset
            if offset is not None:
                result = min(int(offset), result)
        return result if result != sys.maxsize else 0

    def start(self):
        self.task_executor.start()
        for i in range(len(self.workers)):
            self.workers[i].setDaemon(True)
            self.workers[i].setName('schedule_worker_{}'.format(i))
            self.workers[i].start()

    def stop(self):
        self.task_executor.stop()
        for w in self.workers:
            w.stop()
