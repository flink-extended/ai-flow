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
import unittest


from ai_flow.common.configuration import config_constants
from ai_flow.common.env import expand_env_var
from ai_flow.task_executor.kubernetes.kube_config import KubeConfig


class TestKubeConfig(unittest.TestCase):
    def test_kube_config(self):
        config_dict = {
            'pod_template_file': '/foo/bar',
            'image_repository': 'repo/image',
            'image_tag': '0.1',
            'namespace': 'default',
            'in_cluster': True,
            'kube_config_file': '~/.kube/config',
            'client_request_args': {
                'arg1': 'val1',
                'arg2': 'val2'
            }
        }
        kube_config = KubeConfig(config_dict)
        self.assertEqual(kube_config.get_pod_template_file(), '/foo/bar')
        self.assertEqual(kube_config.get_image(), 'repo/image:0.1')
        self.assertEqual(kube_config.get_namespace(), 'default')
        self.assertTrue(kube_config.is_in_cluster())
        self.assertEqual(kube_config.get_config_file(), expand_env_var('~/.kube/config'))
        self.assertEqual(kube_config.get_client_request_args(), {
            'arg1': 'val1',
            'arg2': 'val2'
        })

    def test_default_kube_config(self):
        kube_config = KubeConfig(config_constants.K8S_TASK_EXECUTOR_CONFIG)
        self.assertFalse(kube_config.is_in_cluster())
        self.assertEqual(None, kube_config.get_config_file())
        self.assertEqual(os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            '../../../ai_flow/task_executor/kubernetes/pod_template_file_sample/pod_template.yaml'
        )), kube_config.get_pod_template_file())
