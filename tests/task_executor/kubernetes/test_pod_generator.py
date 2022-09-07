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
import os
import random
import re
import string
import unittest
import uuid
from unittest import mock

from ai_flow.common.exception.exceptions import AIFlowK8sException

from ai_flow.model.task_execution import TaskExecutionKey
from kubernetes.client import ApiClient, models as k8s
from ai_flow.task_executor.kubernetes.pod_generator import PodGenerator
from ai_flow.version import __version__ as version


class TestPodGenerator(unittest.TestCase):
    def setUp(self):
        self.static_uuid = uuid.uuid1()

        self.envs = {'ENVIRONMENT': 'test', 'LOG_LEVEL': 'warning'}

        self.workflow_execution_id = '101'
        self.task_name = 'task_name'
        self.seq_num = 3
        self.try_number = 3
        self.labels = {
            'workflow_execution_id': str(self.workflow_execution_id),
            'task_name': self.task_name,
            'seq_number': str(self.seq_num),
        }
        self.annotations = {
            'workflow_execution_id': str(self.workflow_execution_id),
            'task_name': self.task_name,
            'seq_number': str(self.seq_num),
            'aiflow_version': version,
        }

        self.k8s_client = ApiClient()
        self.expected = k8s.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=k8s.V1ObjectMeta(
                namespace="default",
                name='aiflow-pod.' + self.static_uuid.hex,
                labels={'app': 'aiflow'},
            ),
            spec=k8s.V1PodSpec(
                containers=[
                    k8s.V1Container(
                        name='base',
                        image='base-image',
                        command=['sh', '-c', 'echo Hello Kubernetes!'],
                        env=[
                            k8s.V1EnvVar(name='ENVIRONMENT', value='test'),
                            k8s.V1EnvVar(
                                name="LOG_LEVEL",
                                value='warning',
                            ),
                            k8s.V1EnvVar(
                                name='TARGET',
                                value_from=k8s.V1EnvVarSource(
                                    secret_key_ref=k8s.V1SecretKeySelector(name='secret_b', key='source_b')
                                ),
                            ),
                        ],
                        env_from=[
                            k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name='configmap_a')),
                            k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name='configmap_b')),
                            k8s.V1EnvFromSource(secret_ref=k8s.V1SecretEnvSource(name='secret_a')),
                        ],
                        ports=[k8s.V1ContainerPort(name="foo", container_port=1234)],
                        resources=k8s.V1ResourceRequirements(
                            requests={'memory': '100Mi'},
                            limits={
                                'memory': '200Mi',
                            },
                        ),
                    )
                ],
                security_context=k8s.V1PodSecurityContext(
                    fs_group=2000,
                    run_as_user=1000,
                ),
                host_network=True,
                image_pull_secrets=[
                    k8s.V1LocalObjectReference(name="pull_secret_a"),
                    k8s.V1LocalObjectReference(name="pull_secret_b"),
                ],
            ),
        )

    def test_merge_objects(self):
        base_annotations = {'foo1': 'bar1'}
        base_labels = {'foo1': 'bar1'}
        client_annotations = {'foo2': 'bar2'}
        base_obj = k8s.V1ObjectMeta(annotations=base_annotations, labels=base_labels)
        client_obj = k8s.V1ObjectMeta(annotations=client_annotations)
        res = PodGenerator.merge_objects(base_obj, client_obj)
        client_obj.labels = base_labels
        assert client_obj == res

    def test_extend_object_field(self):
        ports = [k8s.V1ContainerPort(container_port=1, name='port')]
        obj1 = k8s.V1Container(name='c1', ports=ports)
        obj2 = k8s.V1Container(name='c2')
        res = PodGenerator.extend_object_field(obj1, obj2, 'ports')
        self.assertEqual(ports, res.ports)

        ports1 = [k8s.V1ContainerPort(container_port=1, name='p1')]
        obj1 = k8s.V1Container(name='c1', ports=ports1)
        ports2 = [k8s.V1ContainerPort(container_port=1, name='p2')]
        obj2 = k8s.V1Container(name='c2', ports=ports2)
        res = PodGenerator.extend_object_field(obj1, obj2, 'ports')
        self.assertEqual(ports1 + ports2, res.ports)

        obj2 = k8s.V1Container(name='c1', image='image')
        with self.assertRaises(ValueError):
            PodGenerator.extend_object_field(obj1, obj2, 'image')

    def test_reconcile_specs(self):
        spec = k8s.V1PodSpec(containers=[])
        res = PodGenerator.reconcile_specs(spec, None)
        self.assertEqual(spec, res)
        res = PodGenerator.reconcile_specs(None, spec)
        self.assertEqual(spec, res)

        obj1 = [k8s.V1Container(name='container1', image='base_image')]
        obj2 = [k8s.V1Container(name='container2')]
        spec1 = k8s.V1PodSpec(priority=1, active_deadline_seconds=100, containers=obj1)
        spec2 = k8s.V1PodSpec(priority=2, containers=obj2)
        res = PodGenerator.reconcile_specs(spec1, spec2)
        spec2.containers = [k8s.V1Container(name='container2', image='base_image')]
        spec2.active_deadline_seconds = 100
        assert spec2 == res

    @mock.patch('uuid.uuid4')
    def test_reconcile_pods(self, mock_uuid):
        mock_uuid.return_value = self.static_uuid
        path = os.path.join(os.path.dirname(__file__), 'base_pod.yaml')
        base_pod = PodGenerator.get_base_pod_from_template(path)

        mutator_pod = k8s.V1Pod(
            metadata=k8s.V1ObjectMeta(
                name="name2",
                labels={"bar": "baz"},
            ),
            spec=k8s.V1PodSpec(
                containers=[
                    k8s.V1Container(
                        image='',
                        name='name',
                        command=['/bin/command2.sh', 'arg2'],
                        volume_mounts=[
                            k8s.V1VolumeMount(mount_path="/foo/", name="example-kubernetes-test-volume2")
                        ],
                    )
                ],
                volumes=[
                    k8s.V1Volume(
                        host_path=k8s.V1HostPathVolumeSource(path="/tmp/"),
                        name="example-kubernetes-test-volume2",
                    )
                ],
            ),
        )

        result = PodGenerator.reconcile_pods(base_pod, mutator_pod)
        expected: k8s.V1Pod = self.expected
        expected.metadata.name = "name2"
        expected.metadata.labels['bar'] = 'baz'
        expected.spec.volumes = expected.spec.volumes or []
        expected.spec.volumes.append(
            k8s.V1Volume(
                host_path=k8s.V1HostPathVolumeSource(path="/tmp/"), name="example-kubernetes-test-volume2"
            )
        )

        base_container: k8s.V1Container = expected.spec.containers[0]
        base_container.command = ['/bin/command2.sh', 'arg2']
        base_container.volume_mounts = [
            k8s.V1VolumeMount(mount_path="/foo/", name="example-kubernetes-test-volume2")
        ]
        base_container.name = "name"
        expected.spec.containers[0] = base_container

        result_dict = self.k8s_client.sanitize_for_serialization(result)
        expected_dict = self.k8s_client.sanitize_for_serialization(expected)

        assert result_dict == expected_dict

    @mock.patch('uuid.uuid4')
    def test_construct_pod(self, mock_uuid):
        path = os.path.join(os.path.dirname(__file__), 'base_pod.yaml')
        base_pod = PodGenerator.get_base_pod_from_template(path)
        mock_uuid.return_value = self.static_uuid

        result = PodGenerator.construct_pod(
            workflow_execution_id=self.workflow_execution_id,
            task_name=self.task_name,
            seq_num=self.seq_num,
            kube_image='image',
            args=['command'],
            base_worker_pod=base_pod,
            namespace='test_namespace',
        )
        expected = self.expected
        expected.metadata.labels = self.labels
        expected.metadata.labels['app'] = 'aiflow'
        expected.metadata.annotations = self.annotations
        expected.metadata.name = '101-taskname-3.' + self.static_uuid.hex
        expected.metadata.namespace = 'test_namespace'
        expected.spec.containers[0].args = ['command']
        expected.spec.containers[0].image = 'image'
        expected.spec.containers[0].resources = {'requests': {'memory': '100Mi'},
                                                 'limits': {'memory': '200Mi'}}
        result_dict = self.k8s_client.sanitize_for_serialization(result)
        expected_dict = self.k8s_client.sanitize_for_serialization(self.expected)

        self.assertEqual(expected_dict, result_dict)

    def test_deserialize_model(self):
        pod_file = os.path.join(os.path.dirname(__file__), 'pod_for_deserialize.yaml')
        result = PodGenerator.get_base_pod_from_template(pod_file)
        sanitized_res = self.k8s_client.sanitize_for_serialization(result)

        deserialize_result = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'name': 'for-unittest', 'namespace': 'for-unittest'},
            'spec': {
                'containers': [
                    {
                        'args': ['--vm', '1', '--vm-bytes', '150M', '--vm-hang', '1'],
                        'command': ['ps'],
                        'image': 'aiflow/aiflow:latest',
                        'name': 'unittest-ctr',
                        'resources': {'limits': {'memory': '200Mi'}, 'requests': {'memory': '100Mi'}},
                    }
                ]
            },
        }
        self.assertEqual(sanitized_res, deserialize_result)
        with self.assertRaises(AIFlowK8sException):
            PodGenerator.get_base_pod_from_template(None)

    def test_create_pod_id(self):
        keys = [TaskExecutionKey(self._gen_random_string(seed, 200),
                                 self._gen_random_string(seed, 200),
                                 self._gen_random_string(seed, 200)) for seed in range(100)]
        for key in keys:
            pod_name = PodGenerator.create_pod_id(key.workflow_execution_id, key.task_name, key.seq_num)
            self.assertTrue(self._is_valid_pod_id(pod_name))

    @staticmethod
    def _is_valid_pod_id(name):
        regex = r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$"
        return len(name) <= 253 and all(ch.lower() == ch for ch in name) and re.match(regex, name)

    @staticmethod
    def _gen_random_string(seed, str_len):
        char_list = []
        for char_seed in range(str_len):
            random.seed(str(seed) * char_seed)
            char_list.append(random.choice(string.printable))
        return ''.join(char_list)
