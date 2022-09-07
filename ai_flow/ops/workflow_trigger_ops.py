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

import cloudpickle

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.metadata.workflow_event_trigger import WorkflowEventTriggerMeta

from ai_flow.rpc.client.aiflow_client import get_scheduler_client

from ai_flow.model.rule import WorkflowRule

logger = logging.getLogger(__name__)


def add_workflow_trigger(rule: WorkflowRule, workflow_name: str,
                         namespace: str = 'default') -> WorkflowEventTriggerMeta:
    """
    Creates a new workflow event trigger in metadata.

    :param rule: The rule that used to to judge whether start a new workflow execution
    :param workflow_name: The name of the workflow to be registered trigger.
    :param namespace: The namespace of the workflow.
    :return: The WorkflowEventTriggerMeta instance just added.
    """
    client = get_scheduler_client()
    rule_bytes = cloudpickle.dumps(rule)
    client.add_workflow_trigger(namespace=namespace, workflow_name=workflow_name, rule=rule_bytes)


def get_workflow_trigger(trigger_id: int) -> Optional[WorkflowEventTriggerMeta]:
    """
    Retrieves the workflow trigger from metadata.

    :param trigger_id: The id of the trigger.
    :return: The WorkflowEventTriggerMeta instance, return None if no trigger found.
    """
    client = get_scheduler_client()
    return client.get_workflow_trigger(trigger_id)


def list_workflow_triggers(workflow_name: str,
                           namespace: str = 'default',
                           limit: int = None,
                           offset: int = None) -> Optional[List[WorkflowEventTriggerMeta]]:
    """
    Retrieves the list of triggers of the workflow.

    :param workflow_name: The workflow to be listed triggers.
    :param namespace: The namespace which contains the workflow.
    :param limit: The maximum records to be listed.
    :param offset: The offset to start to list.
    :return: The WorkflowEventTriggerMeta list, return None if no workflow trigger found.
    """
    client = get_scheduler_client()
    return client.list_workflow_triggers(namespace=namespace,
                                         workflow_name=workflow_name,
                                         page_size=limit,
                                         offset=offset)


def delete_workflow_trigger(trigger_id):
    """
    Deletes the workflow trigger from metadata.

    :param trigger_id: The id of the workflow trigger.
    :raises: AIFlowException if failed to delete the workflow trigger.
    """
    client = get_scheduler_client()
    try:
        client.delete_workflow_trigger(trigger_id)
    except AIFlowException as e:
        logger.exception("Failed to delete workflow trigger %s with exception %s",
                         str(trigger_id), str(e))
        raise e


def delete_workflow_triggers(workflow_name: str, namespace: str = 'default'):
    """
    Deletes all event triggers of the workflow.

    :param workflow_name: The name of the workflow.
    :param namespace: The namespace which contains the workflow.
    :raises: AIFlowException if failed to delete workflow triggers.
    """
    client = get_scheduler_client()
    try:
        client.delete_workflow_triggers(namespace=namespace, workflow_name=workflow_name)
    except AIFlowException as e:
        logger.exception("Failed to delete triggers of the workflow %s with exception %s",
                         f'{namespace}.{workflow_name}', str(e))
        raise e


def pause_workflow_trigger(trigger_id: int):
    """
    Pauses the workflow trigger.

    :param trigger_id: The id of the workflow trigger.
    :raises: AIFlowException if failed to pause the workflow trigger.
    """
    client = get_scheduler_client()
    try:
        client.pause_workflow_trigger(trigger_id)
    except AIFlowException as e:
        logger.exception("Failed to pause workflow trigger %s with exception %s",
                         str(trigger_id), str(e))
        raise e


def resume_workflow_trigger(trigger_id: int):
    """
    Resumes the workflow trigger which is paused before.

    :param trigger_id: The id of the workflow trigger.
    :raises: AIFlowException if failed to resume the workflow trigger.
    """
    client = get_scheduler_client()
    try:
        client.resume_workflow_trigger(trigger_id)
    except AIFlowException as e:
        logger.exception("Failed to resume workflow trigger %s with exception %s",
                         str(trigger_id), str(e))
        raise e
