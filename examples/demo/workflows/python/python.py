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
from typing import List

from ai_flow_plugins.job_plugins import python
import ai_flow as af
from ai_flow_plugins.job_plugins.python.python_processor import ExecutionContext


# Define the HelloProcessor.
class HelloProcessor(python.PythonProcessor):

    def process(self, execution_context: ExecutionContext, input_list: List) -> List:
        print("Hello World!")
        return []


# Initialize the project and workflow environment.
af.init_ai_flow_context()

# Define a job with job_1 config.
with af.job_config('job_1'):
    # Define the python job.
    af.user_define_operation(processor=HelloProcessor())
