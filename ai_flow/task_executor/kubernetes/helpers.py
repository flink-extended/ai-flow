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
import hashlib
import json
import logging
import re
from typing import Optional, Dict
from kubernetes import client, config

from ai_flow.common.util.local_registry import LocalRegistry
from ai_flow.model.task_execution import TaskExecutionKey

logger = logging.getLogger(__name__)
MAX_LABEL_LEN = 63


def get_kube_client(
    in_cluster: bool = False,
    config_file: Optional[str] = None,
) -> client.CoreV1Api:
    if in_cluster:
        config.load_incluster_config()
    elif config_file is not None:
        config.load_kube_config(config_file=config_file)
    else:
        config.load_kube_config()
    return client.CoreV1Api()


def replace_invalid_chars(string: str) -> str:
    return ''.join(ch.lower() for ch in list(string) if ch.isalnum())


def make_safe_label_value(value):
    """
    Valid label values must be 63 characters or less and must be empty or begin and
    end with an alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores (_),
    dots (.), and alphanumerics between.

    If the label value is greater than 63 chars once made safe, or differs in any
    way from the original value sent to this function, then we need to truncate to
    53 chars, and append it with a unique hash.
    """
    value = str(value)
    safe_label = re.sub(r"^[^a-z0-9A-Z]*|[^a-zA-Z0-9_\-\.]|[^a-z0-9A-Z]*$", "", value)

    if len(safe_label) > MAX_LABEL_LEN or value != safe_label:
        safe_hash = hashlib.md5(value.encode()).hexdigest()[:9]
        safe_label = safe_label[: MAX_LABEL_LEN - len(safe_hash) - 1] + "-" + safe_hash

    return safe_label


def annotations_to_key(annotations: Dict[str, str]) -> TaskExecutionKey:
    workflow_execution_id = int(annotations['workflow_execution_id'])
    task_name = annotations['task_name']
    seq_num = int(annotations['seq_number'])
    return TaskExecutionKey(workflow_execution_id, task_name, seq_num)


def key_to_label_selector(key: TaskExecutionKey) -> str:
    return "workflow_execution_id={}, task_name={}, seq_number={}".format(
        make_safe_label_value(key.workflow_execution_id),
        make_safe_label_value(key.task_name),
        make_safe_label_value(key.seq_num)
    )


def run_pod(core_api: client.CoreV1Api,
            pod: client.V1Pod,
            **kwargs):
    sanitized_pod = core_api.api_client.sanitize_for_serialization(pod)
    json_pod = json.dumps(sanitized_pod, indent=2)
    try:
        resp = core_api.create_namespaced_pod(
            body=sanitized_pod, namespace=pod.metadata.namespace, **kwargs
        )
        return resp
    except Exception as e:
        logger.exception('Exception when attempting to create Namespaced Pod: %s', json_pod)
        raise e
