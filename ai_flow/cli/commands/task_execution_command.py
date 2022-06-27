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
import os
import signal
import threading

from notification_service.embedded_notification_client import EmbeddedNotificationClient

from ai_flow.common.configuration import config_constants
from ai_flow.blob_manager.blob_manager_interface import BlobManagerFactory, BlobManagerConfig
from ai_flow.common.exception.exceptions import TaskFailedException, TaskForceStoppedException
from ai_flow.common.util import workflow_utils
from ai_flow.model.context import Context
from ai_flow.model.internal.events import TaskStatusEvent
from ai_flow.model.operator import AIFlowOperator
from ai_flow.model.status import TaskStatus
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.rpc.client.heartbeat_client import HeartbeatClient
from ai_flow.common.configuration.helpers import AIFLOW_HOME


logging.basicConfig(filename='/Users/alibaba/aiflow/logs/'+__name__+'.log',
                    format='[%(asctime)s-%(filename)s-%(levelname)s:%(message)s]',
                    level=logging.INFO,
                    filemode='a',
                    datefmt='%Y-%m-%d %I:%M:%S %p')
logger = logging.getLogger(__name__)


def run_task_execution(args):
    key = TaskExecutionKey(workflow_execution_id=int(args.workflow_execution_id),
                           task_name=str(args.task_name),
                           seq_num=int(args.sequence_number))
    heartbeat_interval = 10 if args.heartbeat_interval is None else int(args.heartbeat_interval)
    task_manager = TaskManager(workflow_name=args.workflow_name,
                               task_execution_key=key,
                               workflow_snapshot_path=args.snapshot_path,
                               notification_server_uri=args.notification_server_uri,
                               heartbeat_server_uri=args.server_uri,
                               heartbeat_interval=heartbeat_interval)
    try:
        task_manager.start()
        task_manager.run_task()
    finally:
        task_manager.stop()


class TaskManager(object):
    def __init__(self,
                 workflow_name: str,
                 task_execution_key: TaskExecutionKey,
                 workflow_snapshot_path: str,
                 notification_server_uri: str,
                 heartbeat_server_uri: str,
                 heartbeat_interval: int):
        self.workflow_name = workflow_name
        self.task_execution_key = task_execution_key
        self.workflow_snapshot_path = workflow_snapshot_path
        self.notification_client = EmbeddedNotificationClient(
            server_uri=notification_server_uri, namespace='task_status_change', sender='task_manager')
        self.heartbeat_client = HeartbeatClient(heartbeat_server_uri)
        self.heartbeat_thread = threading.Timer(heartbeat_interval, self._send_heartbeat)

    def start(self):
        self.heartbeat_thread.start()

    def run_task(self):
        try:
            self._execute()
        except TaskFailedException:
            self._send_task_status_change(self.task_execution_key, TaskStatus.FAILED)
            raise
        except TaskForceStoppedException:
            self._send_task_status_change(self.task_execution_key, TaskStatus.STOPPED)
            raise
        self._send_task_status_change(self.task_execution_key, TaskStatus.SUCCESS)

    def _execute(self):
        task = self._get_task()
        try:
            if isinstance(task, AIFlowOperator):
                def signal_handler(signum, frame):  # pylint: disable=unused-argument
                    logger.error("Received SIGTERM. Terminating subprocesses.")
                    task.stop()
                    raise TaskForceStoppedException("Task received SIGTERM signal")

                signal.signal(signal.SIGTERM, signal_handler)

                context = Context()
                task.start(context)
                task.await_termination(context)
        except TaskForceStoppedException:
            # self.handle_force_kill()
            raise
        except (Exception, KeyboardInterrupt) as e:
            # self._run_failure_callback()
            raise TaskFailedException(e)
        finally:
            logger.info(f'Task execution {self.task_execution_key} finished, ')

    def _get_task(self):
        # TODO refactor the blob manager to filesystem based
        # Currently we use blob manager to download snapshot, so we need a config file under $AIFLOW_HOME
        # to get config about blob manager, in the future we can download file according to path schema,
        # so that we can save this config file on worker.
        blob_manager = BlobManagerFactory.create_blob_manager(BlobManagerConfig(config_constants.BLOB_MANAGER))
        snapshot_repo = os.path.join(AIFLOW_HOME, 'workflows')

        # TODO download only if we don't have the same snapshot by checking md5
        workflow_snapshot_zip = blob_manager.download(
            remote_file_path=self.workflow_snapshot_path, local_dir=snapshot_repo)
        workflows = workflow_utils.extract_workflows_from_zip(workflow_snapshot_zip, snapshot_repo)
        workflows = [x for x in workflows if x.name == self.workflow_name]
        assert len(workflows) == 1
        return workflows[0].tasks.get(self.task_execution_key.task_name)

    def _send_task_status_change(self, key: TaskExecutionKey, status: TaskStatus):
        event = TaskStatusEvent(workflow_execution_id=key.workflow_execution_id,
                                task_name=key.task_name,
                                sequence_number=key.seq_num,
                                status=status)
        self.notification_client.send_event(event)

    def _send_heartbeat(self):
        logger.debug("Sending heartbeat to task executor.")
        self.heartbeat_client.send_heartbeat(self.task_execution_key)

    def stop(self):
        self.heartbeat_thread.cancel()
        self.heartbeat_thread.join()
        self.notification_client.close()

