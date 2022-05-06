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
import logging
from multiprocessing import Manager
from multiprocessing.managers import SyncManager
from typing import Optional, Tuple

from ai_flow.common.configuration.config_constants import LOCAL_TASK_EXECUTOR_PARALLELISM
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.status import TaskStatus
from ai_flow.common.util.process_utils import stop_process

from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.task_executor.local.worker import CommandType, Worker
from ai_flow.task_executor.task_executor import BaseTaskExecutor


logger = logging.getLogger(__name__)
TaskExecutionCommandType = Tuple[TaskExecutionKey, CommandType]
TaskExecutionStatusType = Tuple[TaskExecutionKey, TaskStatus]


class LocalTaskExecutor(BaseTaskExecutor):

    def __init__(self,
                 parallelism: int = LOCAL_TASK_EXECUTOR_PARALLELISM):
        self.manager: Optional[SyncManager] = None
        self.task_queue: Optional['Queue[TaskExecutionCommandType]'] = None
        self.result_queue: Optional['Queue[TaskExecutionStatusType]'] = None
        self.parallelism = parallelism
        self.workers = []

    def start_task_execution(self, key: TaskExecutionKey) -> str:
        command = self._generate_command(key)
        if not self.task_queue or not self.result_queue:
            raise AIFlowException('LocalTaskExecutor not started.')
        self.task_queue.put((key, command))

    def stop_task_execution(self, key: TaskExecutionKey, handle: str):
        """
        Stop the task execution of specified execution key.

        :param key: Id of the task execution
        :param handle: The handle to identify the task execution process
        """
        try:
            pid = int(handle)
        except ValueError:
            logger.exception('Failed to convert pid with value {}'.format(pid))
        stop_process(pid)

    def start(self):
        """
        Do some initialization, e.g. start a new thread to observe the status
        of all task executions and update the status to metadata backend.
        """
        self.manager = Manager()
        self.task_queue = self.manager.Queue()
        self.result_queue = self.manager.Queue()

        if self.parallelism <= 0:
            raise AIFlowException("Parallelism of LocalTaskExecutor should be a positive integer.")
        self.workers = [
            Worker(self.task_queue, self.result_queue)
            for _ in range(self.parallelism)
        ]
        for worker in self.workers:
            worker.start()

    def stop(self):
        """
        Do some cleanup operations, e.g. stop the observer thread.
        """
        if not self.manager:
            raise AIFlowException("The executor should be started first!")

        for _ in self.workers:
            self.task_queue.put((None, None))
        # Wait for commands to finish
        self.task_queue.join()

        self.manager.shutdown()
