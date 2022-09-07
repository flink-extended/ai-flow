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
from typing import Optional, List

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta

from ai_flow.rpc.client.aiflow_client import get_scheduler_client

logger = logging.getLogger(__name__)


def get_workflow_snapshot(snapshot_id: int) -> Optional[WorkflowSnapshotMeta]:
    """
    Retrieves the workflow snapshot from metadata.

    :param snapshot_id: The id of the snapshot.
    :return: The WorkflowSnapshotMeta instance, return None if no snapshot found.
    """
    client = get_scheduler_client()
    return client.get_workflow_snapshot(snapshot_id)


def list_workflow_snapshots(workflow_name: str,
                            namespace: str = 'default',
                            limit: int = None,
                            offset: int = None) -> Optional[List[WorkflowSnapshotMeta]]:
    """
    Retrieves the list of snapshots of the workflow.

    :param workflow_name: The workflow to be listed.
    :param namespace: The namespace which contains the workflow.
    :param limit: The maximum records to be listed.
    :param offset: The offset to start to list.
    :return: The WorkflowSnapshotMeta list, return None if no workflow snapshots found.
    """
    client = get_scheduler_client()
    return client.list_workflow_snapshots(namespace=namespace,
                                          workflow_name=workflow_name,
                                          page_size=limit,
                                          offset=offset)


def delete_workflow_snapshot(snapshot_id: int):
    """
    Deletes the workflow snapshot from metadata.

    :param snapshot_id: The id of the workflow snapshot.
    :raises: AIFlowException if failed to delete the workflow snapshot.
    """
    client = get_scheduler_client()
    try:
        client.delete_workflow_snapshot(snapshot_id)
    except AIFlowException as e:
        logger.exception("Failed to delete workflow snapshot %s with exception %s",
                         str(snapshot_id), str(e))
        raise e


def delete_workflow_snapshots(workflow_name: str, namespace: str = 'default'):
    """
    Deletes all snapshots of the workflow.

    :param workflow_name: The name of the workflow.
    :param namespace: The namespace which contains the workflow.
    :raises: AIFlowException if failed to delete workflow snapshots.
    """
    client = get_scheduler_client()
    try:
        client.delete_workflow_snapshots(namespace=namespace, workflow_name=workflow_name)
    except AIFlowException as e:
        logger.exception("Failed to delete snapshots of the workflow %s with exception %s",
                         f'{namespace}.{workflow_name}', str(e))
        raise e
