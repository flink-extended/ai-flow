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

from ai_flow import job_config, user_define_operation
from ai_flow.api.ai_flow_context import init_ai_flow_context


class MockProcessor(object):
    """
    MockProcessor is the processor corresponding to the mock job.
    """
    def __init__(self):
        pass


init_ai_flow_context()
with job_config('task_1'):
    user_define_operation(processor=MockProcessor())
with job_config('task_2'):
    user_define_operation(processor=MockProcessor())
