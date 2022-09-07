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
from typing import Dict, List, Optional

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.internal.conditions import SingleEventCondition, TaskStatusCondition, TaskStatusAllMetCondition
from ai_flow.model.operator import Operator
from ai_flow.model.rule import TaskRule
from ai_flow.model.status import TaskStatus


class Workflow(object):
    """
    Workflow is a collection of tasks and trigger rules.
    A Workflow can be scheduled by events, manual or schedule.
    For each execution, the workflow needs to run
    its individual tasks when their triggering rules are met.
    Workflows essentially act as namespaces for tasks. A task_id can only be
    added once to a Workflow.
    """

    def __init__(self,
                 name: str,
                 namespace: str = 'default',
                 **kwargs):
        """
        :param name: The name of the workflow.
        """
        self.name: str = name
        self.config: dict = kwargs
        self.tasks: Dict[str, Operator] = {}
        self.rules: Dict[str, List[TaskRule]] = {}
        self.namespace: str = namespace

    # Context Manager -----------------------------------------------
    def __enter__(self):
        WorkflowContextManager.push_context_managed_workflow(self)
        return self

    def __exit__(self, _type, _value, _tb):
        WorkflowContextManager.pop_context_managed_workflow()

    # Context Manager -----------------------------------------------

    def action_on_condition(self, task_name: str, action: TaskAction, condition: Condition):
        if task_name not in self.rules:
            self.rules[task_name] = []
        self.rules[task_name].append(TaskRule(condition=condition, action=action))

    def action_on_event_received(self, task_name: str, event_key: str, action: TaskAction):
        self.action_on_condition(task_name=task_name,
                                 action=action,
                                 condition=SingleEventCondition(expect_event_key=event_key))

    def action_on_task_status(self,
                              task_name: str,
                              action: TaskAction,
                              upstream_task_status_dict: Dict['Operator', TaskStatus]):
        conditions = []
        for k, v in upstream_task_status_dict.items():
            conditions.append(TaskStatusCondition(namespace=self.namespace,
                                                  workflow_name=self.name,
                                                  task_name=k.name,
                                                  expect_status=v))

        self.action_on_condition(task_name=task_name,
                                 action=action,
                                 condition=TaskStatusAllMetCondition(condition_list=conditions))


class WorkflowContextManager(object):
    """
    Workflow context manager is used to keep the current Workflow when Workflow is used as ContextManager.
    You can use Workflow as context:
    .. code-block:: python
        with Workflow(
            name = 'workflow'
        ) as workflow:
            ...
    If you do this the context stores the Workflow and whenever new task is created, it will use
    such Workflow as the parent Workflow.
    """

    _context_managed_workflow: Optional[Workflow] = None

    @classmethod
    def push_context_managed_workflow(cls, workflow: Workflow):
        if cls._context_managed_workflow is None:
            cls._context_managed_workflow = workflow
        else:
            raise Exception('Sub-workflows are not allowed to be defined in a Workflow.')

    @classmethod
    def pop_context_managed_workflow(cls) -> Optional[Workflow]:
        old_workflow = cls._context_managed_workflow
        cls._context_managed_workflow = None
        return old_workflow

    @classmethod
    def get_current_workflow(cls) -> Optional[Workflow]:
        return cls._context_managed_workflow
