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
import os
from multiprocessing import Manager
from multiprocessing.managers import SyncManager
from typing import Optional, Tuple
from queue import Queue

from ai_flow.common.configuration.config_constants import LOCAL_TASK_EXECUTOR_PARALLELISM
from ai_flow.common.configuration.helpers import get_aiflow_home
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.local_registry import LocalRegistry
from ai_flow.common.util.process_utils import stop_process

from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.task_executor.common.task_executor_base import TaskExecutorBase
from ai_flow.task_executor.local.worker import CommandType, Worker


logger = logging.getLogger(__name__)
TaskExecutionCommandType = Tuple[TaskExecutionKey, CommandType]
MAX_QUEUE_SIZE = 10 * 1024
LOCAL_REGISTRY_PATH = os.path.join(get_aiflow_home(), ".pid_registry")


class LocalTaskExecutor(TaskExecutorBase):

    def __init__(self,
                 parallelism: int = LOCAL_TASK_EXECUTOR_PARALLELISM,
                 registry_path: str = LOCAL_REGISTRY_PATH):
        self.manager: Optional[SyncManager] = None
        self.task_queue: Optional['Queue[TaskExecutionCommandType]'] = None
        self.parallelism = parallelism
        self.workers = []
        self.registry_path = registry_path
        super().__init__()

    def initialize(self):
        if self.parallelism <= 0:
            raise AIFlowException("Parallelism of LocalTaskExecutor should be a positive integer.")
        self.manager = Manager()
        self.task_queue = self.manager.Queue(maxsize=MAX_QUEUE_SIZE)
        self.workers = [
            Worker(self.task_queue, self.registry_path)
            for _ in range(self.parallelism)
        ]
        for worker in self.workers:
            worker.start()

    def destroy(self):
        for _ in self.workers:
            # Send the poison to stop the worker
            self.task_queue.put((None, None))
        if self.task_queue is not None:
            self.task_queue.join()
        if self.manager is not None:
            self.manager.shutdown()

    def start_task_execution(self, key: TaskExecutionKey):
        registry = LocalRegistry(self.registry_path)
        pid = registry.get(str(key))
        if pid is not None:
            logger.warning(f'TaskExecution: {key} has been submitted in the past, skipping...')
            return
        command = self.generate_command(key)
        self.task_queue.put((key, command))

    def stop_task_execution(self, key: TaskExecutionKey):
        """
        Stop the task execution of specified execution key.

        :param key: Id of the task execution
        """
        try:
            registry = LocalRegistry(self.registry_path)
            pid = int(registry.get(str(key)))
        except ValueError:
            logger.exception('Failed to convert pid with value {}'.format(pid))
        stop_process(pid)
