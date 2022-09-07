#
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
import logging

import yaml
from typing import Dict

from ai_flow.common.exception.exceptions import AIFlowYAMLException

logger = logging.getLogger(__name__)


def load_yaml_file(file_path) -> Dict:
    try:
        with open(file_path, "rb") as fd:
            return yaml.safe_load(fd)
    except (IOError, yaml.YAMLError) as exc:
        logger.exception(exc)
        raise AIFlowYAMLException("Failed to load yaml file: {}".format(file_path))


def load_yaml_string(yaml_string) -> Dict:
    try:
        return yaml.safe_load(yaml_string)
    except (IOError, yaml.YAMLError) as exc:
        logger.exception(exc)
        raise AIFlowYAMLException("Failed to load yaml string: {}".format(yaml_string))


def dump_yaml_file(data: Dict, file_path):
    try:
        with open(file_path, 'w') as fd:
            return yaml.dump(data=data, stream=fd, sort_keys=True)
    except (IOError, yaml.YAMLError) as exc:
        logger.exception(exc)
        raise AIFlowYAMLException("Failed to dump yaml file: {}".format(file_path))


