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
import subprocess
from abc import abstractmethod
from multiprocessing import Process
from typing import List, Tuple
from setproctitle import setproctitle
from queue import Queue

from ai_flow.common.configuration import config_constants
from ai_flow.model.status import TaskStatus
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.task_executor.local.local_registry import LocalRegistry

CommandType = List[str]
logger = logging.getLogger(__name__)


class Worker(Process):

    def __init__(self,
                 task_queue,
                 result_queue,
                 registry: LocalRegistry):
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.registry = registry
        super().__init__(target=self.do_work)

    @abstractmethod
    def do_work(self):
        """Called in the subprocess and should then execute tasks"""
        while True:
            key, command = self.task_queue.get()
            try:
                if key is None and command is None:
                    # Received poison pill, no more tasks to run
                    break
                self.execute_work(key=key, command=command)
            finally:
                self.task_queue.task_done()

    def execute_work(self, key: TaskExecutionKey, command: CommandType) -> None:
        if key is None:
            return

        logger.info("Running %s", command)
        if config_constants.EXECUTE_TASKS_IN_NEW_INTERPRETER:
            status = self._execute_in_subprocess(key, command)
        else:
            status = self._execute_in_fork(key, command)

        self.result_queue.put((key, status))

    def _execute_in_subprocess(self, key, command: CommandType) -> TaskStatus:
        process = subprocess.Popen(args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        self.registry.set(str(key), process.pid)
        stdout, stderr = process.communicate()
        retcode = process.poll()
        if retcode:
            logger.error("Return code {} on {} with stdout: {}, stderr: {}".format(
                retcode, " ".join(command), stdout, stderr))
            return TaskStatus.FAILED
        else:
            return TaskStatus.SUCCESS

    def _execute_in_fork(self, key, command: CommandType) -> TaskStatus:
        pid = os.fork()
        if pid:
            self.registry.set(str(key), pid)
            pid, ret = os.waitpid(pid, 0)
            return TaskStatus.SUCCESS if ret == 0 else TaskStatus.FAILED

        ret = 1
        try:
            import signal
            from ai_flow.cli.cli_parser import get_parser

            signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            signal.signal(signal.SIGUSR2, signal.SIG_DFL)

            parser = get_parser()
            args = parser.parse_args(command[1:])
            args.shut_down_logging = False

            setproctitle(f"AIFlow task supervisor: {command}")

            args.func(args)
            ret = 0
            return TaskStatus.SUCCESS
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to execute task %s.", str(e))
        finally:
            logging.shutdown()
            os._exit(ret)
