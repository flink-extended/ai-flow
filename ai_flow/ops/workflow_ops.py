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
# under the License.test_upload_new_workflows
import logging
import os
import sys

import cloudpickle
from pathlib import Path
from typing import List, Optional
from ai_flow.common.util.workflow_utils import upload_workflow_snapshot, extract_workflows_from_file
from ai_flow.metadata import WorkflowMeta

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.rpc.client.aiflow_client import get_scheduler_client

logger = logging.getLogger(__name__)


def upload_workflows(workflow_file_path: str,
                     artifacts: Optional[List[str]] = None) -> List[WorkflowMeta]:
    """
    Upload the workflow defined in `workflow_file_path` along with it's dependencies to AIFlow server.

    :param workflow_file_path: The path of the workflow to be uploaded.
    :param artifacts: The artifacts that the workflow needed.
    :return: The uploaded workflows.
    """
    workflows = extract_workflows_from_file(workflow_file_path)
    if not workflows:
        raise AIFlowException(f'No workflow objects found in {workflow_file_path}, failed to upload workflow.')
    file_hash, uploaded_path = upload_workflow_snapshot(workflow_file_path, artifacts)
    client = get_scheduler_client()
    ret = []
    for workflow in workflows:
        pickled_workflow = cloudpickle.dumps(workflow)
        existed_workflow = client.get_workflow(workflow.name, workflow.namespace)
        if existed_workflow is None:
            workflow_meta = client.add_workflow(name=workflow.name,
                                                namespace=workflow.namespace,
                                                content=Path(workflow_file_path).read_text(),
                                                pickled_workflow=pickled_workflow)
        else:
            workflow_meta = client.update_workflow(namespace=workflow.namespace,
                                                   name=workflow.name,
                                                   content=Path(workflow_file_path).read_text(),
                                                   pickled_workflow=pickled_workflow,
                                                   is_enabled=True)
        client.add_workflow_snapshot(workflow_id=workflow_meta.id,
                                     uri=uploaded_path,
                                     workflow_object=pickled_workflow,
                                     signature=file_hash)
        ret.append(workflow_meta)
    return ret


def get_workflow(workflow_name: str, namespace: str = 'default') -> Optional[WorkflowMeta]:
    """
    Retrieves the workflow from metadata.

    :param workflow_name: The name of the workflow.
    :param namespace: The namespace of the workflow.
    :return: The WorkflowMeta instance, return None if no workflow found.
    """
    client = get_scheduler_client()
    return client.get_workflow(workflow_name, namespace)


def list_workflows(namespace: str = 'default',
                   limit: int = None,
                   offset: int = None) -> Optional[List[WorkflowMeta]]:
    """
    Retrieves the list of workflow of the namespace from metadata.

    :param namespace: The namespace of the workflow.
    :param limit: The maximum records to be listed.
    :param offset: The offset to start to list.
    :return: The WorkflowMeta list, return None if no workflow found.
    """
    client = get_scheduler_client()
    return client.list_workflows(namespace, page_size=limit, offset=offset)


def delete_workflow(workflow_name: str, namespace: str = 'default'):
    """
    Deletes the workflow from metadata, also its executions, schedules and triggers would be cascade deleted,
    however if not-finished workflow execution found, the deletion would be interrupted.

    :param workflow_name: The name of the workflow.
    :param namespace: The namespace of the workflow.
    :raises: AIFlowException if failed to delete the workflow.
    """
    client = get_scheduler_client()
    try:
        while True:
            executions = client.list_workflow_executions(namespace=namespace,
                                                         workflow_name=workflow_name,
                                                         page_size=10)
            if executions is not None:
                for e in executions:
                    logger.info(f"Removing workflow execution {e.id}")
                    client.delete_workflow_execution(e.id)
            else:
                break
        logger.info("Cascade deleting workflow schedules...")
        client.delete_workflow_schedules(namespace=namespace, workflow_name=workflow_name)

        logger.info('Cascade deleting workflow triggers...')
        client.delete_workflow_triggers(namespace=namespace, workflow_name=workflow_name)

        logger.info('Cascade deleting workflow snapshots...')
        client.delete_workflow_snapshots(namespace=namespace, workflow_name=workflow_name)
        client.delete_workflow(name=workflow_name, namespace=namespace)
    except AIFlowException as e:
        logger.exception("Failed to delete workflow %s with exception %s", f'{namespace}.{workflow_name}', str(e))
        raise e


def disable_workflow(workflow_name: str, namespace: str = 'default'):
    """
    Disables the workflow so that no more executions would be started, however,
    the existed executions are not effected.

    :param workflow_name: The name of the workflow.
    :param namespace: The namespace of the workflow.
    :raises: AIFlowException if failed to disable workflow.
    """
    client = get_scheduler_client()
    try:
        client.disable_workflow(name=workflow_name, namespace=namespace)
    except AIFlowException as e:
        logger.exception("Failed to disable workflow %s with exception %s", f'{namespace}.{workflow_name}', str(e))
        raise e


def enable_workflow(workflow_name: str, namespace: str = 'default'):
    """
    Enables the workflow.

    :param workflow_name: The name of the workflow.
    :param namespace: The namespace of the workflow.
    :raises: AIFlowException if failed to enable workflow.
    """
    client = get_scheduler_client()
    try:
        client.enable_workflow(name=workflow_name, namespace=namespace)
    except AIFlowException as e:
        logger.exception("Failed to enable workflow %s with exception %s", f'{namespace}.{workflow_name}', str(e))
        raise e
