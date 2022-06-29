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
import logging
import cloudpickle
from pathlib import Path
from typing import List, Optional
from ai_flow.common.util.workflow_utils import upload_workflow_snapshot, extract_workflows_from_file
from ai_flow.metadata import WorkflowMeta, NamespaceMeta, WorkflowExecutionMeta

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.rpc.client.aiflow_client import get_ai_flow_client

logger = logging.getLogger(__name__)


def get_workflow(namespace: str, workflow_name: str) -> Optional[WorkflowMeta]:
    client = get_ai_flow_client()
    return client.get_workflow(workflow_name, namespace)


def add_namespace(name: str, properties: dict) -> NamespaceMeta:
    client = get_ai_flow_client()
    return client.add_namespace(name, properties)


def start_workflow_execution(workflow_name: str,
                             namespace: str = 'default') -> WorkflowExecutionMeta:
    """
    :param workflow_name: The workflow to be execute.
    :param namespace: The namespace which contains the workflow.
    :return: The WorkflowExecution just started.
    """
    client = get_ai_flow_client()
    client.start_workflow_execution(workflow_name, namespace)


def upload_workflows(workflow_file_path: str,
                     artifacts: Optional[List[str]] = None) -> List[WorkflowMeta]:
    """
    :param workflow_file_path: The path of the workflow to be uploaded.
    :param artifacts: The artifacts that the workflow needed.
    :param namespace: The namespace which the workflow is uploaded to.
    :return: The uploaded workflows.
    """
    workflows = extract_workflows_from_file(workflow_file_path)
    if not workflows:
        raise AIFlowException(f'No workflow objects found in {workflow_file_path}, failed to upload workflow.')
    file_hash, uploaded_path = upload_workflow_snapshot(workflow_file_path, artifacts)
    client = get_ai_flow_client()
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



