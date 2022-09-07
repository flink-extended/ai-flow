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
import threading
from abc import abstractmethod
from queue import Empty
from typing import Optional

from ai_flow.rpc.client.aiflow_client import get_notification_client

from ai_flow.common.util.db_util.session import create_session
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.metadata.workflow import WorkflowMeta

from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta

from ai_flow.common.configuration.config_constants import NOTIFICATION_SERVER_URI, INTERNAL_RPC_PORT, \
    TASK_HEARTBEAT_INTERVAL
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.net_utils import get_ip_addr
from ai_flow.common.util.thread_utils import StoppableThread
from ai_flow.metadata.message import PersistentQueue
from ai_flow.model.action import TaskAction
from ai_flow.model.internal.events import TaskStatusEvent, TaskStatusChangedEvent
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
        self.heartbeat_manager: HeartbeatManager = None

    def schedule_task(self, command: TaskScheduleCommand):
        if not self.command_queue:
            raise AIFlowException('TaskExecutor not started.')
        self.command_queue.put(command)

    def start(self):
        logging.info("starting task executor.")
        self.command_queue = PersistentQueue(maxsize=MAX_QUEUE_SIZE)
        self.command_processor.start()
        self.heartbeat_manager = HeartbeatManager()
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

    def _send_task_status_change(self, key: TaskExecutionKey, status: TaskStatus):
        workflow_meta = self._get_workflow(key.workflow_execution_id)
        if not workflow_meta:
            logging.exception(f"No workflow meta exists with execution id: {key.workflow_execution_id}")
        else:
            client = None
            try:
                client = get_notification_client(namespace=workflow_meta.namespace, sender='task_executor')
                event_for_meta = TaskStatusEvent(workflow_execution_id=key.workflow_execution_id,
                                                 task_name=key.task_name,
                                                 sequence_number=key.seq_num,
                                                 status=status)
                client.send_event(event_for_meta)
                workflow = self._get_workflow(key.workflow_execution_id)
                event_for_schedule = TaskStatusChangedEvent(workflow_name=workflow.name,
                                                            workflow_execution_id=key.workflow_execution_id,
                                                            task_name=key.task_name,
                                                            status=status,
                                                            namespace=workflow.namespace)
                client.send_event(event_for_schedule)
            finally:
                client.close()

    def _process_command(self):
        # TODO put command processor in an Actor or thread pool with order preserving
        while not threading.current_thread().stopped():
            try:
                schedule_command = self.command_queue.get(timeout=1)
                try:
                    current_task = schedule_command.current_task_execution
                    new_task = schedule_command.new_task_execution
                    action = schedule_command.action
                    if action == TaskAction.START:
                        logger.info("Running {} command on {}".format(action, new_task))
                        self.start_task_execution(new_task)
                    elif action == TaskAction.STOP:
                        logger.info("Running {} command on {}".format(action, current_task))
                        self.stop_task_execution(current_task)
                        self._send_task_status_change(current_task, TaskStatus.STOPPED)
                    elif action == TaskAction.RESTART:
                        logger.info("Running {} command on {}".format(action, current_task))
                        if current_task is not None:
                            self.stop_task_execution(current_task)
                            self._send_task_status_change(current_task, TaskStatus.STOPPED)
                        self.start_task_execution(new_task)
                except Exception as e:
                    logger.exception("Error occurred while processing command queue, {}".format(e))
                finally:
                    self.command_queue.remove_expired()
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

    def generate_command(self, key: TaskExecutionKey):
        workflow = self._get_workflow(key.workflow_execution_id)
        if workflow is None:
            raise AIFlowException(f'Cannot find corresponding workflow for task {key}.')
        workflow_snapshot = self._get_workflow_snapshot(workflow.id)
        if workflow_snapshot is None:
            raise AIFlowException(f'Cannot find workflow snapshot for task {key}.')
        return ["aiflow",
                "taskmanager",
                "run",
                str(workflow.name),
                str(key.workflow_execution_id),
                str(key.task_name),
                str(key.seq_num),
                str(workflow_snapshot.uri),
                NOTIFICATION_SERVER_URI,
                '{}:{}'.format(get_ip_addr(), INTERNAL_RPC_PORT),
                '--heartbeat-interval', str(TASK_HEARTBEAT_INTERVAL)
                ]

    @staticmethod
    def _get_workflow_snapshot(workflow_id) -> Optional[WorkflowSnapshotMeta]:
        """
        Get the location of the snapshot of the workflow execution

        :param workflow_id: Id of the workflow
        :return: The WorkflowSnapshotMeta
        """
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            snapshot = metadata_manager.get_latest_snapshot(workflow_id)
            return snapshot

    @staticmethod
    def _get_workflow(workflow_execution_id) -> Optional[WorkflowMeta]:
        """
        Get the name of the workflow by the execution id

        :param workflow_execution_id: Id of the workflow execution
        :return: The WorkflowMeta
        """
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_execution = metadata_manager.get_workflow_execution(workflow_execution_id)
            if workflow_execution is not None:
                workflow = metadata_manager.get_workflow_by_id(workflow_execution.workflow_id)
                return workflow
            else:
                return None
