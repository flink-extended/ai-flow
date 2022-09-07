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
import logging
import subprocess
from abc import abstractmethod
from multiprocessing import Process
from typing import List

from ai_flow.common.util.local_registry import LocalRegistry
from ai_flow.model.status import TaskStatus
from ai_flow.model.task_execution import TaskExecutionKey

CommandType = List[str]
logger = logging.getLogger(__name__)


class Worker(Process):

    def __init__(self,
                 task_queue,
                 registry_path):
        self.task_queue = task_queue
        self.registry_path = registry_path
        super().__init__(target=self.do_work)

    @abstractmethod
    def do_work(self):
        """Called in the subprocess and should then execute tasks"""
        while True:
            task, command = self.task_queue.get()
            try:
                if task is None and command is None:
                    logger.info('Poison received, breaking the loop...')
                    break
                self.execute_work(key=task, command=command)
            finally:
                self.task_queue.task_done()

    def execute_work(self, key: TaskExecutionKey, command: CommandType) -> None:
        if key is None:
            return
        logger.info("Running %s", command)
        self._execute_in_subprocess(key, command)

    def _execute_in_subprocess(self, key, command: CommandType) -> TaskStatus:
        process = subprocess.Popen(args=command,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   close_fds=True,
                                   bufsize=-1,
                                   universal_newlines=True)
        LocalRegistry(self.registry_path).set(str(key), process.pid)
        stdout, stderr = process.communicate()
        retcode = process.poll()
        if retcode:
            command = ' '.join(command)
            logger.error(f"Return code {retcode} on {command}")
            logger.error(f"stdout: {stdout}")
            logger.error(f"stderr: {stderr}")
            return TaskStatus.FAILED
        else:
            return TaskStatus.SUCCESS
