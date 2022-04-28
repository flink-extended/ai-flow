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
from typing import Dict, List

from ai_flow.model.operator import Operator
from ai_flow.model.rule import TaskRule


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
                 **kwargs):
        """
        :param name: The name of the workflow.
        """
        self.name: str = name
        self.config: dict = kwargs
        self.tasks: Dict[str, Operator] = {}
        self.rules: Dict[str, List[TaskRule]] = {}
