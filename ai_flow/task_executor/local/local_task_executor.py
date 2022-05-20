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
import threading
from multiprocessing import Manager
from multiprocessing.managers import SyncManager
from typing import Optional, Tuple
from queue import Queue, Empty

from ai_flow.common.configuration.config_constants import LOCAL_TASK_EXECUTOR_PARALLELISM
from ai_flow.common.configuration.helpers import get_aiflow_home
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.thread_utils import StoppableThread
from ai_flow.model.status import TaskStatus
from ai_flow.common.util.process_utils import stop_process

from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.task_executor.local.local_registry import LocalRegistry
from ai_flow.task_executor.local.worker import CommandType, Worker
from ai_flow.task_executor.task_executor import BaseTaskExecutor


logger = logging.getLogger(__name__)
TaskExecutionCommandType = Tuple[TaskExecutionKey, CommandType]
TaskExecutionStatusType = Tuple[TaskExecutionKey, TaskStatus]
MAX_QUEUE_SIZE = 10 * 1024
LOCAL_REGISTRY_PATH = os.path.join(get_aiflow_home(), ".pid_registry")


class LocalTaskExecutor(BaseTaskExecutor):

    def __init__(self,
                 parallelism: int = LOCAL_TASK_EXECUTOR_PARALLELISM,
                 registry_path: str = LOCAL_REGISTRY_PATH):
        self.manager: Optional[SyncManager] = None
        self.task_queue: Optional['Queue[TaskExecutionCommandType]'] = None
        self.result_queue: Optional['Queue[TaskExecutionStatusType]'] = None
        self.parallelism = parallelism
        self.workers = []
        self._task_status_observer = StoppableThread(target=self._update_status)
        self.registry = LocalRegistry(registry_path)

    def start_task_execution(self, key: TaskExecutionKey):
        command = ["aiflow", "task-execution", "run",
                   str(key.workflow_execution_id),
                   str(key.task_name),
                   str(key.seq_num)]
        if not self.task_queue or not self.result_queue:
            raise AIFlowException('LocalTaskExecutor not started.')
        self.task_queue.put((key, command))

    def stop_task_execution(self, key: TaskExecutionKey):
        """
        Stop the task execution of specified execution key.

        :param key: Id of the task execution
        """
        try:
            pid = int(self.registry.get(str(key)))
        except ValueError:
            logger.exception('Failed to convert pid with value {}'.format(pid))
        stop_process(pid)

    def start(self):
        """
        Do some initialization, e.g. start a new thread to observe the status
        of all task executions and update the status to metadata backend.
        """
        if self.parallelism <= 0:
            raise AIFlowException("Parallelism of LocalTaskExecutor should be a positive integer.")

        self.manager = Manager()
        self.task_queue = self.manager.Queue(maxsize=MAX_QUEUE_SIZE)
        self.result_queue = self.manager.Queue(maxsize=MAX_QUEUE_SIZE)
        self._task_status_observer.start()

        self.workers = [
            Worker(self.task_queue, self.result_queue, self.registry)
            for _ in range(self.parallelism)
        ]
        for worker in self.workers:
            worker.start()
        self.recover()

    def stop(self):
        """
        Do some cleanup operations, e.g. stop the observer thread.
        """
        if not self.manager:
            raise AIFlowException("The executor should be started first!")

        self._task_status_observer.stop()
        self._task_status_observer.join()

        for _ in self.workers:
            self.task_queue.put((None, None))
        # Wait for commands to finish
        self.task_queue.join()
        self.manager.shutdown()



    def recover(self):
        # TODO recover state
        pass

    def _update_status(self):
        while not threading.current_thread().stopped():
            try:
                key, status = self.result_queue.get(timeout=1)
                self.registry.remove(str(key))
                # TODO call scheduler interface to save meta
                print("Save task execution {} with status {} to meta".format(key, status))
            except Empty:
                pass
            except Exception as e:
                logger.exception("Error occurred when update task status, {}".format(e))
        logger.info("TaskStatusUpdateThread exiting")
