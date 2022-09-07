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
import logging
from abc import abstractmethod, ABC

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.module_utils import import_string
from ai_flow.scheduler.schedule_command import TaskScheduleCommand

logger = logging.getLogger(__name__)


class TaskExecutor(ABC):

    @abstractmethod
    def schedule_task(self, command: TaskScheduleCommand):
        """
        Start, stop or restart the task.

        :param command: The command that contains information to schedule a task.
        """

    @abstractmethod
    def start(self):
        """
        Do some initialization.
        """

    @abstractmethod
    def stop(self):
        """
        Do some cleanup operations.
        """


class TaskExecutorFactory(object):

    @classmethod
    def get_class_name(cls, executor_type: str):
        executors = {
            'local': 'ai_flow.task_executor.local.local_task_executor.LocalTaskExecutor',
            'kubernetes': 'ai_flow.task_executor.kubernetes.k8s_task_executor.KubernetesTaskExecutor'
        }
        if executor_type.lower() in executors:
            return executors[executor_type.lower()]
        else:
            raise AIFlowException("Invalid task executor type: {}".format(executor_type))

    @classmethod
    def get_task_executor(cls, executor_type: str) -> TaskExecutor:
        class_name = cls.get_class_name(executor_type)
        class_object = import_string(class_name)
        return class_object()
