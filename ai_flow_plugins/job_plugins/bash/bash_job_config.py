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
from typing import Dict, Text, Optional

from ai_flow import ExecutionMode, Jsonable
from ai_flow.workflow.job_config import JobConfig


class BashJobConfig(JobConfig):
    """
    BashJobConfig is the configuration of the bash job.
    It has a configuration item env, which represents the environment variables of the bash job.
    Example:
        job_name:
            job_type: bash
            properties:
                env:
                    a: a
                    b: b
    """
    def __init__(self, job_name: Text = None,
                 job_label_report_interval: float = 5.0,
                 properties: Dict[Text, Jsonable] = None) -> None:
        super().__init__(job_name, 'bash', job_label_report_interval, properties)

    @property
    def env(self):
        return self.properties.get('env')
