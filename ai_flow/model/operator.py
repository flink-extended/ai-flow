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
from abc import abstractmethod

from typing import Dict, Optional

from ai_flow.model.context import Context
from ai_flow.model.status import TaskStatus


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
                 inputs: list = None,
                 outputs: list = None,
                 **kwargs,
                 ):
        """
        :param name: The operator's name.
        :param inputs: Operator input parameters.
        :param outputs: Operator output parameters.
        :param kwargs: Operator's extended parameters.
        """
        self.name: str = name
        self.config: dict = kwargs
        self.inputs = inputs
        self.outputs = outputs
        self.workflow = None  # The workflow to which the operator belongs.


class AIFlowOperator(Operator):
    """
    AIFlowOperator is a template that defines a task, it defines AIFlow's native Operator interface.
    To derive this class, you are expected to override the constructor as well as abstract methods.
    """

    def __init__(self,
                 task_name: str,
                 inputs: list = None,
                 outputs: list = None,
                 **kwargs):
        super().__init__(task_name, inputs, outputs, **kwargs)

    @abstractmethod
    def start(self, context: Context):
        """Start a task instance."""
        pass

    @abstractmethod
    def stop(self, context: Context):
        """Stop a task instance."""
        pass

    @abstractmethod
    def await_termination(self, context: Context, timeout: Optional[int] = None):
        """Wait for a task instance to finish.
        :param context: The context in which the operator is executed.
        :param timeout: If timeout is None, wait until the task ends.
                        If timeout is not None, wait for the task to end or the time exceeds timeout(seconds).
        """
        pass

    @abstractmethod
    def get_status(self, context: Context) -> TaskStatus:
        """Get the status of a task instance."""
        pass

    @abstractmethod
    def get_metrics(self, context: Context) -> Dict:
        """Get the metrics of a task instance."""
        pass
