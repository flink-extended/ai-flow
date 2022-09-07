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

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.metadata.workflow_execution import WorkflowExecutionMeta

from ai_flow.rpc.client.aiflow_client import get_scheduler_client

logger = logging.getLogger(__name__)


def start_workflow_execution(workflow_name: str,
                             namespace: str = 'default') -> int:
    """
    Start a new execution of the workflow.

    :param workflow_name: The workflow to be executed.
    :param namespace: The namespace which contains the workflow.
    :return: Id of the workflow execution just started.
    :raises: AIFlowException if failed to start workflow execution.
    """
    client = get_scheduler_client()
    try:
        return client.start_workflow_execution(workflow_name, namespace)
    except AIFlowException as e:
        logger.exception("Failed to start execution for workflow %s with exception %s",
                         f'{namespace}.{workflow_name}', str(e))
        raise e


def stop_workflow_execution(workflow_execution_id: int):
    """
    Asynchronously stop the execution of the workflow.

    :param workflow_execution_id: The id of workflow execution to be stopped.
    :raises: AIFlowException if failed to stop the workflow execution.
    """
    client = get_scheduler_client()
    try:
        client.stop_workflow_execution(workflow_execution_id)
    except AIFlowException as e:
        logger.exception("Failed to stop workflow execution %s with exception %s",
                         str(workflow_execution_id), str(e))
        raise e


def stop_workflow_executions(workflow_name: str, namespace: str = 'default'):
    """
    Asynchronously stop all executions of the workflow.

    :param workflow_name: The workflow to be stopped.
    :param namespace: The namespace which contains the workflow.
    :raises: AIFlowException if failed to stop workflow executions.
    """
    client = get_scheduler_client()
    try:
        client.stop_workflow_executions(namespace=namespace, workflow_name=workflow_name)
    except AIFlowException as e:
        logger.exception("Failed to stop all executions of workflow %s with exception %s",
                         f'{namespace}.{workflow_name}', str(e))
        raise e


def get_workflow_execution(workflow_execution_id: int) -> Optional[WorkflowExecutionMeta]:
    """
    Retrieves the workflow execution from metadata.

    :param workflow_execution_id: The id of the workflow execution.
    :return: The WorkflowExecutionMeta instance, return None if no execution found.
    """
    client = get_scheduler_client()
    return client.get_workflow_execution(workflow_execution_id)


def list_workflow_executions(workflow_name: str,
                             namespace: str = 'default',
                             limit: int = None,
                             offset: int = None) -> Optional[List[WorkflowExecutionMeta]]:
    """
    Retrieves the list of executions of the workflow.

    :param workflow_name: The workflow to be listed.
    :param namespace: The namespace which contains the workflow.
    :param limit: The maximum records to be listed.
    :param offset: The offset to start to list.
    :return: The WorkflowExecutionMeta list, return None if no workflow execution found.
    """

    client = get_scheduler_client()
    return client.list_workflow_executions(namespace=namespace,
                                           workflow_name=workflow_name,
                                           page_size=limit,
                                           offset=offset)


def delete_workflow_execution(workflow_execution_id: int):
    """
    Deletes the workflow execution from metadata, note that the workflow
    execution to be deleted should be finished.

    :param workflow_execution_id: The id of the workflow execution.
    :raises: AIFlowException if failed to delete the workflow execution.
    """
    client = get_scheduler_client()
    try:
        client.delete_workflow_execution(workflow_execution_id)
    except AIFlowException as e:
        logger.exception("Failed to delete workflow execution %s with exception %s",
                         str(workflow_execution_id), str(e))
        raise e
