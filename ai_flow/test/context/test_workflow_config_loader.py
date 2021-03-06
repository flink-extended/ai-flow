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
import unittest
import os
from ai_flow.context.workflow_config_loader import init_workflow_config, current_workflow_config


class TestWorkflowConfigLoader(unittest.TestCase):

    def test_workflow_context(self):
        workflow_file = os.path.join(os.path.dirname(__file__), 'workflow_1.yaml')
        init_workflow_config(workflow_file)
        workflow_config = current_workflow_config()
        self.assertEqual('workflow_1', workflow_config.workflow_name)
        self.assertEqual(3, len(workflow_config.job_configs))


if __name__ == '__main__':
    unittest.main()
