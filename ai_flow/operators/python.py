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
from typing import Optional, Callable, List, Dict

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.context import Context
from ai_flow.model.operator import AIFlowOperator


class PythonOperator(AIFlowOperator):

    def __init__(self,
                 name: str,
                 python_callable: Callable,
                 op_args: Optional[List] = None,
                 op_kwargs: Optional[Dict] = None,
                 **kwargs):
        super().__init__(name, **kwargs)
        if not callable(python_callable):
            raise AIFlowException('`python_callable` param must be callable')
        self.python_callable = python_callable
        self.op_args = op_args or []
        self.op_kwargs = op_kwargs or {}

    def start(self, context: Context):
        self.python_callable(*self.op_args, **self.op_kwargs)
