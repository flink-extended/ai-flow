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
"""taskmanager command"""
import logging
import os
import signal
from contextlib import contextmanager, redirect_stdout, redirect_stderr

from ai_flow.common.configuration import config_constants
from ai_flow.blob_manager.blob_manager_interface import BlobManagerFactory, BlobManagerConfig
from ai_flow.common.exception.exceptions import TaskFailedException, TaskForceStoppedException
from ai_flow.common.util import workflow_utils
from ai_flow.common.util.log_util.log_writer import StreamLogWriter
from ai_flow.common.util.thread_utils import RepeatedTimer
from ai_flow.model.internal.contexts import TaskExecutionContext
from ai_flow.model.internal.events import TaskStatusEvent, TaskStatusChangedEvent
from ai_flow.model.operator import AIFlowOperator
from ai_flow.model.status import TaskStatus
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.rpc.client.aiflow_client import get_notification_client
from ai_flow.rpc.client.heartbeat_client import HeartbeatClient
from ai_flow.common.configuration.helpers import AIFLOW_HOME
from ai_flow.model.internal.contexts import set_runtime_task_context

logger = logging.getLogger('aiflow.task')


def set_logger_context(logger, workflow_name, task_execution_key):
    for i in logger.handlers:
        i.set_context(workflow_name, task_execution_key)


@contextmanager
def _capture_task_logs():
    """
    Replace the root logger configuration with the aiflow.task configuration
    so we can capture logs from any custom loggers used in the task.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logger.level)
    root_logger.handlers[:] = logger.handlers

    info_writer = StreamLogWriter(logger, logging.INFO)
    warning_writer = StreamLogWriter(logger, logging.WARNING)

    with redirect_stdout(info_writer), redirect_stderr(warning_writer):
        yield


def run_task_manager(args):
    key = TaskExecutionKey(workflow_execution_id=int(args.workflow_execution_id),
                           task_name=str(args.task_name),
                           seq_num=int(args.sequence_number))
    set_logger_context(logger, args.workflow_name, key)
    heartbeat_interval = 10 if args.heartbeat_interval is None else int(args.heartbeat_interval)
    task_manager = TaskManager(workflow_name=args.workflow_name,
                               task_execution_key=key,
                               workflow_snapshot_path=args.snapshot_path,
                               notification_server_uri=args.notification_server_uri,
                               heartbeat_server_uri=args.server_uri,
                               heartbeat_interval=heartbeat_interval)
    try:
        task_manager.start()
        with _capture_task_logs():
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
        self.namespace = None
        self.workflow_name = workflow_name
        self.task_execution_key = task_execution_key
        self.workflow_snapshot_path = workflow_snapshot_path

        self.workflow = self._extract_workflow()
        self.namespace = self.workflow.namespace
        self.context = TaskExecutionContext(self.workflow, self.task_execution_key)

        self.notification_client = get_notification_client(
            notification_server_uri=notification_server_uri, namespace=self.namespace, sender='task_manager')
        self.heartbeat_client = HeartbeatClient(heartbeat_server_uri)
        self.heartbeat_thread = RepeatedTimer(heartbeat_interval, self._send_heartbeat)

    def start(self):
        self.heartbeat_thread.start()

    def run_task(self):
        try:
            self._send_task_status_change(TaskStatus.RUNNING)
            self._execute()
        except TaskFailedException:
            self._send_task_status_change(TaskStatus.FAILED)
            raise
        except TaskForceStoppedException:
            raise
        else:
            self._send_task_status_change(TaskStatus.SUCCESS)

    def _execute(self):
        task = self.workflow.tasks.get(self.task_execution_key.task_name)
        set_runtime_task_context(self.context)
        context = self.context
        try:
            if isinstance(task, AIFlowOperator):
                def signal_handler(signum, frame):  # pylint: disable=unused-argument
                    logger.error("Received SIGTERM. Terminating subprocesses.")
                    task.stop(context)
                    raise TaskForceStoppedException("Task received SIGTERM signal")
                signal.signal(signal.SIGTERM, signal_handler)
                task.start(self.context)
                task.await_termination(self.context)
        except TaskForceStoppedException:
            raise
        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            raise TaskFailedException(e)
        finally:
            logger.info(f'Task execution {self.task_execution_key} finished, ')

    def _get_working_dir(self):
        workflow_execution_id = self.task_execution_key.workflow_execution_id
        working_dir = os.path.join(AIFLOW_HOME,
                                   'working_dir',
                                   self.workflow_name,
                                   str(workflow_execution_id))
        if not os.path.exists(working_dir):
            os.makedirs(working_dir, exist_ok=False)
        return working_dir

    def _extract_workflow(self):
        # TODO refactor the blob manager to filesystem based
        # Currently we use blob manager to download snapshot, so we need a config file under $AIFLOW_HOME
        # to get config about blob manager, in the future we can download file according to path schema,
        # so that we can save this config file on worker.
        blob_manager = BlobManagerFactory.create_blob_manager(BlobManagerConfig(config_constants.BLOB_MANAGER))
        snapshot_repo = os.path.join(AIFLOW_HOME, 'snapshots')
        if not os.path.isdir(snapshot_repo):
            os.makedirs(snapshot_repo)

        # TODO download only if we don't have the same snapshot by checking md5
        workflow_snapshot_zip = blob_manager.download(
            remote_file_path=self.workflow_snapshot_path, local_dir=snapshot_repo
        )
        working_dir = self._get_working_dir()
        workflow_list = workflow_utils.extract_workflows_from_zip(workflow_snapshot_zip, working_dir)
        workflow = [x for x in workflow_list if x.name == self.workflow_name][0]
        return workflow

    def _send_task_status_change(self, status: TaskStatus):
        event_for_meta = TaskStatusEvent(workflow_execution_id=self.task_execution_key.workflow_execution_id,
                                         task_name=self.task_execution_key.task_name,
                                         sequence_number=self.task_execution_key.seq_num,
                                         status=status)
        self.notification_client.send_event(event_for_meta)
        event_for_schedule = TaskStatusChangedEvent(workflow_name=self.workflow_name,
                                                    workflow_execution_id=self.task_execution_key.workflow_execution_id,
                                                    task_name=self.task_execution_key.task_name,
                                                    status=status,
                                                    namespace=self.namespace)
        self.notification_client.send_event(event_for_schedule)

    def _send_heartbeat(self):
        logger.info("Sending heartbeat to task executor.")
        try:
            self.heartbeat_client.send_heartbeat(self.task_execution_key)
        except Exception as e:
            logger.exception(e)
            raise e

    def stop(self):
        self.heartbeat_thread.cancel()
        self.heartbeat_thread.join()
        self.notification_client.close()
