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
import time
import grpc
from concurrent import futures

from ai_flow.common.util.db_util.session import create_session
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.rpc.client.aiflow_client import get_notification_client

from ai_flow.rpc.protobuf.message_pb2 import Response, SUCCESS

from ai_flow.common.configuration import config_constants
from ai_flow.model.internal.events import TaskHeartbeatTimeoutEvent

from ai_flow.model.status import TaskStatus, TASK_FINISHED_SET
from ai_flow.common.util.thread_utils import StoppableThread
from ai_flow.metadata.task_execution import TaskExecutionMeta
from ai_flow.rpc.protobuf import heartbeat_service_pb2_grpc

logger = logging.getLogger(__name__)


class HeartbeatManager(object):
    def __init__(self):
        self.task_dict = {}
        self._update_running_tasks()

        self.heartbeat_timeout = config_constants.TASK_HEARTBEAT_TIMEOUT
        self.heartbeat_check_interval = config_constants.TASK_EXECUTOR_HEARTBEAT_CHECK_INTERVAL

        self.service = HeartbeatService(self.task_dict)
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
        heartbeat_service_pb2_grpc.add_HeartbeatServiceServicer_to_server(self.service, self.grpc_server)
        self.grpc_server.add_insecure_port('[::]:{}'.format(config_constants.INTERNAL_RPC_PORT))
        self.notification_client = None
        self.heartbeat_check_thread = StoppableThread(target=self._check_heartbeat_timeout)

    def start(self):
        self.notification_client = get_notification_client(sender='aiflow_heartbeat_manager')

        self.grpc_server.start()
        logger.info('Heartbeat Service started.')
        self.heartbeat_check_thread.start()

    def stop(self):
        self.heartbeat_check_thread.stop()
        self.heartbeat_check_thread.join()
        self.grpc_server.stop(0)
        self.notification_client.close()
        logging.info('Heartbeat Service stopped.')

    def _update_running_tasks(self):
        with create_session() as session:
            running_tasks = session.query(TaskExecutionMeta).filter(
                TaskExecutionMeta.status == TaskStatus.RUNNING).all()

            for task in running_tasks:
                key = TaskExecutionKey(workflow_execution_id=task.workflow_execution_id,
                                       task_name=task.task_name,
                                       seq_num=task.sequence_number)
                if str(key) not in self.task_dict:
                    self.task_dict.update({str(key): time.time()})

    def _check_heartbeat_timeout(self):
        while not threading.current_thread().stopped():
            now = time.time()
            for key, last_heartbeat in dict(self.task_dict).items():
                if now - last_heartbeat > self.heartbeat_timeout:
                    task_execution = self._string_to_task_execution_key(key)
                    task_status = self._get_task_status(task_execution)
                    if task_status is None:
                        logger.error('TaskExecution {} not found in database.'.format(task_execution))
                    elif task_status not in TASK_FINISHED_SET:
                        logger.warning('Task: {} heartbeat timeout, notifying scheduler.'.format(task_execution))
                        self._send_heartbeat_timeout(task_execution)
                        self.task_dict.pop(key)
                    else:
                        self.task_dict.pop(key)
            self._update_running_tasks()
            time.sleep(self.heartbeat_check_interval)

    @staticmethod
    def _string_to_task_execution_key(string: str) -> TaskExecutionKey:
        first = string.index('_')
        last = string.rindex('_')
        return TaskExecutionKey(workflow_execution_id=string[:first],
                                task_name=string[first + 1: last],
                                seq_num=string[last + 1:])

    @staticmethod
    def _get_task_status(key: TaskExecutionKey):
        with create_session() as session:
            return session.query(TaskExecutionMeta.status).filter(
                TaskExecutionMeta.workflow_execution_id == key.workflow_execution_id,
                TaskExecutionMeta.task_name == key.task_name,
                TaskExecutionMeta.sequence_number == key.seq_num).scalar()

    def _send_heartbeat_timeout(self, key: TaskExecutionKey):
        with create_session() as session:
            task_execution = session.query(TaskExecutionMeta).filter(
                TaskExecutionMeta.workflow_execution_id == key.workflow_execution_id,
                TaskExecutionMeta.task_name == key.task_name,
                TaskExecutionMeta.sequence_number == key.seq_num).first()
            if not task_execution:
                logger.warning('TaskExecution {} not found in database.'.format(key))
            else:
                event = TaskHeartbeatTimeoutEvent(workflow_execution_id=task_execution.workflow_execution_id,
                                                  task_name=task_execution.task_name,
                                                  sequence_number=task_execution.sequence_number)
                self.notification_client.send_event(event)


class HeartbeatService(heartbeat_service_pb2_grpc.HeartbeatServiceServicer):
    def __init__(self, task_dict):
        self.task_dict = task_dict

    def send_heartbeat(self, request, context):
        key = TaskExecutionKey(workflow_execution_id=request.workflow_execution_id,
                               task_name=request.task_name,
                               seq_num=request.sequence_number)
        if str(key) in self.task_dict:
            self.task_dict.update({str(key): time.time()})
        return Response(return_code=str(SUCCESS))
