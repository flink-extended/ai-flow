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
from typing import List
import time
from ai_flow_plugins.job_plugins import python
from ai_flow_plugins.job_plugins.python.python_processor import ExecutionContext
from ai_flow import current_workflow_config


class PyProcessor1(python.PythonProcessor):

    def process(self, execution_context: ExecutionContext, input_list: List) -> List:
        print("Zhang san hello world!")
        word_count_file = os.path.dirname(__file__) + "/../../resources/word_count.txt"
        print(os.path.abspath(word_count_file))
        with open(word_count_file, 'r') as f:
            print(f.read())
        print(current_workflow_config().job_configs['task_1'].properties['a'])
        return []


class PyProcessor2(python.PythonProcessor):

    def process(self, execution_context: ExecutionContext, input_list: List) -> List:
        print("Li si hello world!")
        time.sleep(100)
        return []