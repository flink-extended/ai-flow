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
import os
from typing import Dict

from ai_flow.common.env import expand_env_var
from ai_flow.common.exception.exceptions import AIFlowConfigException


class KubeConfig:

    def __init__(self, config: Dict):
        if config is None:
            raise AIFlowConfigException('The kubernetes option is not configured.')
        self.config = config

    def get_pod_template_file(self) -> str:
        default_template = os.path.join(os.path.dirname(__file__),
                                        'pod_template_file_sample/pod_template.yaml')
        template = self.config.get('pod_template_file')
        return template if template else default_template

    def get_image(self) -> str:
        repository = self.config.get('image_repository')
        tag = self.config.get('image_tag')
        return f'{repository}:{tag}'

    def get_namespace(self) -> str:
        return self.config.get('namespace', 'default')

    def get_client_request_args(self) -> dict:
        return self.config.get('client_request_args', {})

    def get_delete_options(self) -> dict:
        return self.config.get('delete_options', {})

    def is_in_cluster(self) -> bool:
        return self.config.get('in_cluster', False)

    def get_config_file(self) -> str:
        path = self.config.get('kube_config_file', None)
        return expand_env_var(path)
