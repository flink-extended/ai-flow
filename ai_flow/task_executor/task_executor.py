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
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime

from typing import List

from ai_flow.common.exception.exceptions import AIFlowDBException
from ai_flow.model.action import TaskAction
from ai_flow.model.status import TaskStatus
from ai_flow.common.util.db_util.session import create_session
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.task_execution import TaskExecution, TaskExecutionKey

logger = logging.getLogger(__name__)


class ScheduleTaskCommand(object):
    def __init__(self,
                 task_execution: TaskExecutionKey,
                 action: TaskAction):
        self.task_execution = task_execution
        self.action = action

    def __str__(self):
        return "task_execution: {0} action: {1}".format(self.task_execution, self.action)


class BaseTaskExecutor(ABC):

    def __init__(self):
        pass

    def schedule_task(self, command: ScheduleTaskCommand):
        if command.action == TaskAction.START:
            self.start_task_execution(command.task_execution)
        elif command.action == TaskAction.STOP:
            self.stop_task_execution(command.task_execution)
        elif command.action == TaskAction.RESTART:
            self.stop_task_execution(command.task_execution)
            self.start_task_execution(command.task_execution)

    def start_task_execution(self, key: TaskExecutionKey) -> str:
        """
        Start the task execution on worker.

        :param key: Id of the task execution
        :return: The handle of the submitted task execution, which can be used to stop the task execution
        """
        raise NotImplementedError()

    @abstractmethod
    def stop_task_execution(self, key: TaskExecutionKey, handle: str):
        """
        Stop the task execution of specified execution key.

        :param key: Id of the task execution
        :param handle: The handle to identify the task execution process
        """
        raise NotImplementedError()

    @abstractmethod
    def start(self):
        """
        Do some initialization, e.g. start a new thread to observe the status
        of all task executions and update the status to metadata backend.
        """
        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        """
        Do some cleanup operations, e.g. stop the observer thread.
        """
        raise NotImplementedError()
