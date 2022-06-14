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
"""task-execution command"""
import logging
import threading
import time

from notification_service.embedded_notification_client import EmbeddedNotificationClient

from ai_flow.common.configuration import config_constants
from ai_flow.common.exception.exceptions import TaskFailedException, TaskForceStoppedException
from ai_flow.model.internal.events import TaskStatusEvent
from ai_flow.model.status import TaskStatus
from ai_flow.model.task_execution import TaskExecution, TaskExecutionKey
from ai_flow.rpc.client.heartbeat_client import HeartbeatClient

logger = logging.getLogger(__name__)


def run_task_execution(args):

    task_execution = TaskExecution(workflow_execution_id=args.workflow_execution_id,
                                   task_name=args.task_name,
                                   sequence_number=args.seq_num,
                                   execution_type=args.execution_type)
    task_manager = TaskManager(task_execution=task_execution,
                               notification_server_uri=args.notification_server_uri,
                               heartbeat_server_uri=args.heartbeat_server_uri,
                               heartbeat_interval=args.heartbeat_interval)
    try:
        task_manager.start()
        task_manager.run_task()
    finally:
        task_manager.stop()


class TaskManager(object):
    def __init__(self,
                 task_execution,
                 notification_server_uri,
                 heartbeat_server_uri,
                 heartbeat_interval):
        self.task_execution = task_execution
        self.heartbeat_interval = heartbeat_interval
        self.notification_client = EmbeddedNotificationClient(
            server_uri=notification_server_uri, namespace='task_status_change', sender='task_manager')
        self.heartbeat_client = HeartbeatClient(heartbeat_server_uri)
        self.heartbeat_thread = threading.Thread(target=self._heartbeat, daemon=True)

    def start(self):
        self.heartbeat_thread.start()

    def run_task(self):
        try:
            self.task_execution.run()
        except TaskFailedException:
            self._send_task_status_change(self.task_execution, TaskStatus.FAILED)
            raise
        except TaskForceStoppedException:
            self._send_task_status_change(self.task_execution, TaskStatus.STOPPED)
            raise
        self._send_task_status_change(self.task_execution, TaskStatus.SUCCESS)

    def _send_task_status_change(self, task: TaskExecutionKey, status: TaskStatus):
        event = TaskStatusEvent(workflow_execution_id=task.workflow_execution_id,
                                task_name=task.task_name,
                                sequence_number=task.seq_num,
                                status=status)
        self.notification_client.send_event(event)

    def _heartbeat(self):
        while not threading.current_thread().stopped():
            logger.debug("Sending heartbeat to task executor.")
            self.heartbeat_client.send_heartbeat(self.task_execution.workflow_execution_id,
                                                 self.task_execution.task_name,
                                                 self.task_execution.sequence_number)
            time.sleep(self.heartbeat_interval)

    def stop(self):
        self.notification_client.close()
        self.heartbeat_thread.stop()
        self.heartbeat_thread.join()

