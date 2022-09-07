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
from typing import List

from ai_flow.model.rule import TaskRule, WorkflowRule


class TaskRuleWrapper(object):
    """It is a rule for a task."""
    def __init__(self, task_name, rules: List[TaskRule]):
        self.task_name = task_name
        self.rules = rules


class WorkflowExecutionRuleWrapper(object):
    """It is a rule for a workflow execution."""
    def __init__(self, workflow_execution_id: int, task_rule_wrappers: List[TaskRuleWrapper]):
        self.workflow_execution_id = workflow_execution_id
        self.task_rule_wrappers = task_rule_wrappers


class WorkflowRuleWrapper(object):
    """It is a rule for a workflow."""
    def __init__(self, workflow_id: int, rules: List[WorkflowRule]):
        self.workflow_id = workflow_id
        self.rules = rules
