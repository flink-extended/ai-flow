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
import threading
from abc import abstractmethod
from queue import Empty

from notification_service.notification_client import NotificationClient

from ai_flow.common.configuration.config_constants import NOTIFICATION_SERVER_URI
from notification_service.embedded_notification_client import EmbeddedNotificationClient

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.thread_utils import StoppableThread
from ai_flow.metadata.message import PersistentQueue

from ai_flow.model.action import TaskAction
from ai_flow.model.internal.events import TaskStatusEvent
from ai_flow.model.status import TaskStatus
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.scheduler.schedule_command import TaskScheduleCommand
from ai_flow.task_executor.common.heartbeat_manager import HeartbeatManager
from ai_flow.task_executor.task_executor import TaskExecutor

MAX_QUEUE_SIZE = 10 * 1024
logger = logging.getLogger(__name__)


class TaskExecutorBase(TaskExecutor):

    def __init__(self):
        self.command_queue: PersistentQueue = None
        self.command_processor = StoppableThread(target=self._process_command)
        self.notification_client: NotificationClient = None
        self.heartbeat_manager: HeartbeatManager = None

    def schedule_task(self, command: TaskScheduleCommand):
        if not self.command_queue:
            raise AIFlowException('TaskExecutor not started.')
        self.command_queue.put(command)
        task = command.current_task_execution
        if command.action == TaskAction.START:
            self._send_task_status_change(task=task, status=TaskStatus.QUEUED)
        elif command.action == TaskAction.STOP:
            self._send_task_status_change(task=task, status=TaskStatus.STOPPING)
        elif command.action == TaskAction.RESTART:
            self._send_task_status_change(task=task, status=TaskStatus.RESTARTING)

    def start(self):
        self.notification_client = EmbeddedNotificationClient(
            server_uri=NOTIFICATION_SERVER_URI, namespace='task_status_change', sender='task_executor')
        self.command_queue = PersistentQueue(maxsize=MAX_QUEUE_SIZE)
        self.command_processor.start()
        self.heartbeat_manager = HeartbeatManager(self.notification_client)
        self.heartbeat_manager.start()
        self.initialize()

    def stop(self):
        if not self.command_queue:
            raise AIFlowException("The executor should be started first!")
        self.destroy()
        self.heartbeat_manager.stop()
        self.command_processor.stop()
        self.command_processor.join()
        self.command_queue.join()
        self.notification_client.close()

    def _send_task_status_change(self, task: TaskExecutionKey, status: TaskStatus):
        event = TaskStatusEvent(workflow_execution_id=task.workflow_execution_id,
                                task_name=task.task_name,
                                sequence_number=task.seq_num,
                                status=status)
        self.notification_client.send_event(event)

    def _process_command(self):
        # TODO put command processor in an Actor or thread pool with order preserving
        while not threading.current_thread().stopped():
            try:
                schedule_command = self.command_queue.get(timeout=1)
                try:
                    current_task = schedule_command.current_task_execution
                    action = schedule_command.action
                    logger.info("Running {} command on {}".format(action, current_task))

                    if action == TaskAction.START:
                        self.start_task_execution(current_task)
                        self._send_task_status_change(task=current_task, status=TaskStatus.RUNNING)
                    elif action == TaskAction.STOP:
                        self.stop_task_execution(current_task)
                    elif action == TaskAction.RESTART:
                        self.stop_task_execution(current_task)
                        new_task = schedule_command.new_task_execution
                        self.start_task_execution(new_task)
                        self._send_task_status_change(task=new_task, status=TaskStatus.RUNNING)
                    self.command_queue.remove_expired()
                except Exception as e:
                    logger.exception("Error occurred while processing command queue, {}".format(e))
                finally:
                    self.command_queue.task_done()
            except Empty:
                pass

    def initialize(self):
        pass

    def destroy(self):
        pass

    @abstractmethod
    def start_task_execution(self, key: TaskExecutionKey):
        """
        Start the task execution by key
        """

    @abstractmethod
    def stop_task_execution(self, key: TaskExecutionKey):
        """
        Stop the task execution by key.
        """

    @staticmethod
    def generate_command(key: TaskExecutionKey):
        return ["aiflow",
                "task-execution",
                "run",
                str(key.workflow_execution_id),
                str(key.task_name),
                str(key.seq_num)
                ]
