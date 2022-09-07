#
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
#
import yaml
from typing import Dict, Text


class AIFlowConfiguration(Dict[Text, Text]):

    def load_from_file(self, file_path):
        with open(file_path, 'r') as f:
            yaml_config = yaml.load(f, Loader=yaml.FullLoader)
            self.update(yaml_config.items())

    def dump_to_file(self, file_path):
        with open(file_path, 'w') as f:
            return yaml.dump(data=dict(self), stream=f)
