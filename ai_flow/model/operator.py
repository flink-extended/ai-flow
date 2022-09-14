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
import logging
from abc import abstractmethod
from typing import Dict, Optional, List, Union

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.status import TaskStatus


class OperatorConfigItem(object):
    """
    The Operator's config items.
    PERIODIC_EXPRESSION: The expression for the periodic task.
    """
    PERIODIC_EXPRESSION = 'periodic_expression'


class Operator(object):
    """
    Operator is a template that defines a task. It is the abstract base class for all operators.
    Since operators create objects that become tasks in the Workflow.To derive this class, you are expected to override
    the constructor method.
    This class is abstract and shouldn't be instantiated. Instantiating a class derived from this one results in
    the creation of a task object, which ultimately becomes a task in Workflow objects.
    """

    def __init__(self,
                 name: str,
                 **kwargs,
                 ):
        """
        :param name: The operator's name.
        :param kwargs: Operator's extended parameters.
        """
        from ai_flow.model.workflow import WorkflowContextManager
        self.name: str = name
        self.config: dict = kwargs
        self.workflow = WorkflowContextManager.get_current_workflow()  # The workflow to which the operator belongs.
        self.workflow.tasks[self.name] = self

    def action_on_condition(self, action: TaskAction, condition: Condition):
        """
        Schedule the task based on a specified condition.
        :param action: The action for scheduling the task.
        :param condition: The condition for scheduling the task to depend on.
        """
        self.workflow.action_on_condition(task_name=self.name, action=action, condition=condition)

    def action_on_event_received(self, action: TaskAction, event_key: str):
        """
        When the specified event is received, the task is scheduled.
        :param action: The action for scheduling the task.
        :param event_key: The event for scheduling the task to depend on.
        """
        self.workflow.action_on_event_received(task_name=self.name, event_key=event_key, action=action)

    def action_on_task_status(self,
                              action: TaskAction,
                              upstream_task_status_dict: Dict['Operator', TaskStatus]):
        """
        Schedule the task based on the status of upstream tasks.
        :param action: The action for scheduling the task.
        :param upstream_task_status_dict: The upstream task status for scheduling the task to depend on.
        """
        self.workflow.action_on_task_status(task_name=self.name,
                                            action=action,
                                            upstream_task_status_dict=upstream_task_status_dict)

    def start_after(self, tasks: Union['Operator', List['Operator']]):
        """
        Start the task after upstream tasks succeed.
        :param tasks: The upstream tasks.
        """
        task_list = []
        if isinstance(tasks, List):
            task_list.extend(tasks)
        else:
            task_list.append(tasks)
        task_status = dict.fromkeys(task_list, TaskStatus.SUCCESS)
        self.action_on_task_status(TaskAction.START, task_status)


class AIFlowOperator(Operator):
    """
    AIFlowOperator is a template that defines a task, it defines AIFlow's native Operator interface.
    To derive this class, you are expected to override the constructor as well as abstract methods.
    """

    def __init__(self,
                 task_name: str,
                 **kwargs):
        super().__init__(task_name, **kwargs)
        self.log = logging.getLogger('aiflow.task.operator')

    @abstractmethod
    def start(self, context: Context):
        """Start a task instance."""
        pass

    def stop(self, context: Context):
        """Stop a task instance."""
        pass

    def await_termination(self, context: Context, timeout: Optional[int] = None):
        """Wait for a task instance to finish.
        :param context: The context in which the operator is executed.
        :param timeout: If timeout is None, wait until the task ends.
                        If timeout is not None, wait for the task to end or the time exceeds timeout(seconds).
        """
        pass

    def get_metrics(self, context: Context) -> Dict:
        """Get the metrics of a task instance."""
        pass
