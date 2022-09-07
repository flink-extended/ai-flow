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
from typing import List, Optional

from ai_flow.metadata.task_execution import TaskExecutionMeta

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.rpc.client.aiflow_client import get_scheduler_client

logger = logging.getLogger(__name__)


def start_task_execution(workflow_execution_id: int,
                         task_name: str) -> str:
    """
    Start a new execution of the task.

    :param workflow_execution_id: The workflow execution contains the task.
    :param task_name: The name of the task to be started.
    :return: The TaskExecutionKey str.
    :raises: AIFlowException if failed to start task execution.
    """
    client = get_scheduler_client()
    try:
        return client.start_task_execution(workflow_execution_id, task_name)
    except AIFlowException as e:
        logger.exception("Failed to start execution for task %s with exception %s",
                         f'{workflow_execution_id}.{task_name}', str(e))
        raise e


def stop_task_execution(workflow_execution_id: int,
                        task_name: str):
    """
    Asynchronously stop the task execution.

    :param workflow_execution_id: The workflow execution contains the task.
    :param task_name: The name of the task to be stopped.
    :raises: AIFlowException if failed to stop task execution.
    """
    client = get_scheduler_client()
    try:
        client.stop_task_execution(workflow_execution_id, task_name)
    except AIFlowException as e:
        logger.exception("Failed to stop task execution %s with exception %s",
                         f'{workflow_execution_id}.{task_name}', str(e))
        raise e


def get_task_execution(task_execution_id: int) -> TaskExecutionMeta:
    """
    Retrieves the task execution from metadata.

    :param task_execution_id: The id of the task execution.
    :return: The TaskExecutionMeta instance, return None if no execution found.
    """
    client = get_scheduler_client()
    return client.get_task_execution(task_execution_id)


def list_task_executions(workflow_execution_id: int,
                         limit: int = None,
                         offset: int = None) -> Optional[List[TaskExecutionMeta]]:
    """
    Retrieves the list of executions of the task of the workflow execution.

    :param workflow_execution_id: The id of the workflow execution.
    :param limit: The maximum records to be listed.
    :param offset: The offset to start to list.
    :return: The TaskExecutionMeta list, return None if no task execution found.
    """
    client = get_scheduler_client()
    return client.list_task_executions(workflow_execution_id=workflow_execution_id,
                                       page_size=limit,
                                       offset=offset)
