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
from ai_flow.rpc.client.aiflow_client import get_scheduler_client

from ai_flow.metadata.workflow_schedule import WorkflowScheduleMeta

logger = logging.getLogger(__name__)


def add_workflow_schedule(expression: str, workflow_name: str,
                          namespace: str = 'default') -> WorkflowScheduleMeta:
    """
    Creates a new workflow schedule in metadata.

    :param expression: The string express when the workflow execution is triggered.
                       Two types of expression are supported here: cron and interval.
                       cron_expression:
                            cron@minute, hour, day of month, month, day of week
                            See https://en.wikipedia.org/wiki/Cron for more information on the format accepted here.
                       interval_expression:
                            interval@days hours minutes seconds
                            e.g. "interval@0 1 0 0" means running every 1 hour since now.
    :param workflow_name: The name of the workflow to be registered schedule.
    :param namespace: The namespace of the workflow.
    :return: The WorkflowScheduleMeta instance just added.
    """
    client = get_scheduler_client()
    return client.add_workflow_schedule(namespace=namespace,
                                        workflow_name=workflow_name,
                                        expression=expression)


def get_workflow_schedule(schedule_id: int) -> Optional[WorkflowScheduleMeta]:
    """
    Retrieves the workflow schedule from metadata.

    :param schedule_id: The id of the schedule.
    :return: The WorkflowScheduleMeta instance, return None if no schedule found.
    """
    client = get_scheduler_client()
    return client.get_workflow_schedule(schedule_id)


def list_workflow_schedules(workflow_name: str,
                            namespace: str = 'default',
                            limit: int = None,
                            offset: int = None) -> Optional[List[WorkflowScheduleMeta]]:
    """
    Retrieves the list of schedules of the workflow.

    :param workflow_name: The workflow to be listed schedules.
    :param namespace: The namespace which contains the workflow.
    :param limit: The maximum records to be listed.
    :param offset: The offset to start to list.
    :return: The WorkflowScheduleMeta list, return None if no workflow schedules found.
    """
    client = get_scheduler_client()
    return client.list_workflow_schedules(namespace=namespace,
                                          workflow_name=workflow_name,
                                          page_size=limit,
                                          offset=offset)


def delete_workflow_schedule(schedule_id):
    """
    Deletes the workflow schedule from metadata.

    :param schedule_id: The id of the workflow schedule.
    :raises: AIFlowException if failed to delete the workflow schedule.
    """
    client = get_scheduler_client()
    try:
        client.delete_workflow_schedule(schedule_id)
    except AIFlowException as e:
        logger.exception("Failed to delete workflow schedule %s with exception %s",
                         str(schedule_id), str(e))
        raise e


def delete_workflow_schedules(workflow_name: str, namespace: str = 'default'):
    """
    Deletes all schedules of the workflow.

    :param workflow_name: The name of the workflow.
    :param namespace: The namespace which contains the workflow.
    :raises: AIFlowException if failed to delete workflow schedules.
    """
    client = get_scheduler_client()
    try:
        client.delete_workflow_schedules(namespace=namespace, workflow_name=workflow_name)
    except AIFlowException as e:
        logger.exception("Failed to delete schedules of the workflow %s with exception %s",
                         f'{namespace}.{workflow_name}', str(e))
        raise e


def pause_workflow_schedule(schedule_id: int):
    """
    Pauses the workflow schedule.

    :param schedule_id: The id of the workflow schedule.
    :raises: AIFlowException if failed to pause the workflow schedule.
    """
    client = get_scheduler_client()
    try:
        client.pause_workflow_schedule(schedule_id)
    except AIFlowException as e:
        logger.exception("Failed to pause workflow schedule %s with exception %s",
                         str(schedule_id), str(e))
        raise e


def resume_workflow_schedule(schedule_id: int):
    """
    Resumes the workflow schedule which is paused before.

    :param schedule_id: The id of the workflow schedule.
    :raises: AIFlowException if failed to resume the workflow schedule.
    """
    client = get_scheduler_client()
    try:
        client.resume_workflow_schedule(schedule_id)
    except AIFlowException as e:
        logger.exception("Failed to resume workflow schedule %s with exception %s",
                         str(schedule_id), str(e))
        raise e
