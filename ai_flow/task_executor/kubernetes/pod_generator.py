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
import copy
import os
import uuid
import yaml

from functools import reduce
from typing import List, Optional

from ai_flow.model.task_execution import TaskExecutionKey
from kubernetes.client import models as k8s
from kubernetes.client.api_client import ApiClient

from ai_flow.common.exception.exceptions import AIFlowK8sException
from ai_flow.task_executor.kubernetes.helpers import make_safe_label_value, replace_invalid_chars
from ai_flow.version import __version__ as version

MAX_LABEL_LEN = 63


class PodGenerator:

    @staticmethod
    def construct_pod(
            workflow_execution_id: int,
            task_name: str,
            seq_num: int,
            kube_image: str,
            args: List[str],
            base_worker_pod: k8s.V1Pod,
            namespace: str,
    ) -> k8s.V1Pod:
        dynamic_pod = k8s.V1Pod(
            metadata=k8s.V1ObjectMeta(
                namespace=namespace,
                annotations={
                    'workflow_execution_id': str(workflow_execution_id),
                    'task_name': str(task_name),
                    'seq_number': str(seq_num),
                    'aiflow_version': version,
                },
                name=PodGenerator.create_pod_id(workflow_execution_id, task_name, seq_num),
                labels={
                    'workflow_execution_id': make_safe_label_value(workflow_execution_id),
                    'task_name': make_safe_label_value(task_name),
                    'seq_number': make_safe_label_value(seq_num),
                },
            ),
            spec=k8s.V1PodSpec(
                containers=[
                    k8s.V1Container(
                        name="base",
                        args=args,
                        image=kube_image,
                    )
                ]
            ),
        )
        return reduce(PodGenerator.reconcile_pods, [base_worker_pod, dynamic_pod])

    @staticmethod
    def get_base_pod_from_template(path: str) -> k8s.V1Pod:
        if not path or not os.path.isfile(path):
            raise AIFlowK8sException(
                f"Could not find a valid template yaml at '{path}'"
            )
        else:
            with open(path) as stream:
                pod = yaml.safe_load(stream)

        return PodGenerator.deserialize_model_dict(pod)

    @staticmethod
    def deserialize_model_dict(pod_dict: dict) -> k8s.V1Pod:
        api_client = ApiClient()
        return api_client._ApiClient__deserialize_model(pod_dict, k8s.V1Pod)

    @staticmethod
    def reconcile_pods(base_pod: k8s.V1Pod, user_pod: Optional[k8s.V1Pod]) -> k8s.V1Pod:
        if user_pod is None:
            return base_pod

        user_pod_cp = copy.deepcopy(user_pod)
        user_pod_cp.spec = PodGenerator.reconcile_specs(base_pod.spec, user_pod_cp.spec)
        user_pod_cp.metadata = PodGenerator.reconcile_metadata(base_pod.metadata, user_pod_cp.metadata)
        user_pod_cp = PodGenerator.merge_objects(base_pod, user_pod_cp)
        return user_pod_cp

    @staticmethod
    def reconcile_metadata(base_meta, user_meta):
        if base_meta and not user_meta:
            return base_meta
        if not base_meta and user_meta:
            return user_meta
        elif user_meta and base_meta:
            user_meta.labels = PodGenerator.merge_objects(base_meta.labels, user_meta.labels)
            user_meta.annotations = PodGenerator.merge_objects(base_meta.annotations, user_meta.annotations)
            PodGenerator.extend_object_field(base_meta, user_meta, 'managed_fields')
            PodGenerator.extend_object_field(base_meta, user_meta, 'finalizers')
            PodGenerator.extend_object_field(base_meta, user_meta, 'owner_references')
            return PodGenerator.merge_objects(base_meta, user_meta)

        return None

    @staticmethod
    def reconcile_specs(
        base_spec: Optional[k8s.V1PodSpec], user_spec: Optional[k8s.V1PodSpec]
    ) -> Optional[k8s.V1PodSpec]:
        if base_spec and not user_spec:
            return base_spec
        if not base_spec and user_spec:
            return user_spec
        elif user_spec and base_spec:
            user_spec.containers = PodGenerator.reconcile_containers(
                base_spec.containers, user_spec.containers
            )
            merged_spec = PodGenerator.extend_object_field(base_spec, user_spec, 'volumes')
            return PodGenerator.merge_objects(base_spec, merged_spec)

        return None

    @staticmethod
    def reconcile_containers(
        base_containers: List[k8s.V1Container], user_containers: List[k8s.V1Container]
    ) -> List[k8s.V1Container]:
        if not base_containers:
            return user_containers
        if not user_containers:
            return base_containers

        user_container = user_containers[0]
        base_container = base_containers[0]
        user_container = PodGenerator.extend_object_field(base_container, user_container, 'volume_mounts')
        user_container = PodGenerator.extend_object_field(base_container, user_container, 'env')
        user_container = PodGenerator.extend_object_field(base_container, user_container, 'env_from')
        user_container = PodGenerator.extend_object_field(base_container, user_container, 'ports')
        user_container = PodGenerator.extend_object_field(base_container, user_container, 'volume_devices')
        user_container = PodGenerator.merge_objects(base_container, user_container)

        return [user_container] + PodGenerator.reconcile_containers(
            base_containers[1:], user_containers[1:]
        )

    @staticmethod
    def merge_objects(base_obj, user_obj):
        if not base_obj:
            return user_obj
        if not user_obj:
            return base_obj

        user_obj_cp = copy.deepcopy(user_obj)

        if isinstance(base_obj, dict) and isinstance(user_obj_cp, dict):
            base_obj_cp = copy.deepcopy(base_obj)
            base_obj_cp.update(user_obj_cp)
            return base_obj_cp

        for base_key in base_obj.to_dict().keys():
            base_val = getattr(base_obj, base_key, None)
            if not getattr(user_obj, base_key, None) and base_val:
                if not isinstance(user_obj_cp, dict):
                    setattr(user_obj_cp, base_key, base_val)
                else:
                    user_obj_cp[base_key] = base_val
        return user_obj_cp

    @staticmethod
    def create_pod_id(workflow_execution_id, task_name, seq_num) -> str:
        workflow_execution_id = replace_invalid_chars(str(workflow_execution_id))
        task_name = replace_invalid_chars(str(task_name))
        seq_num = replace_invalid_chars(str(seq_num))
        readable_pod_id = f'{workflow_execution_id}-{task_name}-{seq_num}'
        return PodGenerator.make_unique_pod_id(readable_pod_id)

    @staticmethod
    def make_unique_pod_id(pod_id: str) -> str:
        """
        Kubernetes pod names must consist of one or more lowercase
        rfc1035/rfc1123 labels separated by '.' with a maximum length of 253
        characters. Each label has a maximum length of 63 characters.

        Name must pass the following regex for validation
        ``^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$``

        For more details, see:
        https://github.com/kubernetes/kubernetes/blob/release-1.1/docs/design/identifiers.md

        :param pod_id: a dag_id with only alphanumeric characters
        :return: ``str`` valid Pod name of appropriate length
        """
        if not pod_id:
            return None

        safe_uuid = uuid.uuid4().hex  # safe uuid will always be less than 63 chars
        trimmed_pod_id = pod_id[:MAX_LABEL_LEN]
        safe_pod_id = f"{trimmed_pod_id}.{safe_uuid}"

        return safe_pod_id

    @staticmethod
    def extend_object_field(base_obj, user_obj, field_name):
        user_obj_cp = copy.deepcopy(user_obj)
        base_obj_field = getattr(base_obj, field_name, None)
        user_obj_field = getattr(user_obj, field_name, None)

        if (not isinstance(base_obj_field, list) and base_obj_field is not None) or (
                not isinstance(user_obj_field, list) and user_obj_field is not None
        ):
            raise ValueError("The chosen field must be a list.")

        if not base_obj_field:
            return user_obj_cp
        if not user_obj_field:
            setattr(user_obj_cp, field_name, base_obj_field)
            return user_obj_cp

        appended_fields = base_obj_field + user_obj_field
        setattr(user_obj_cp, field_name, appended_fields)
        return user_obj_cp
