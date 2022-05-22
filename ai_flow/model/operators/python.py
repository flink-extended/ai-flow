#
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
#
import logging
from typing import Optional, Callable, List
from multiprocessing import Process

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.context import Context
from ai_flow.model.operator import AIFlowOperator

logger = logging.getLogger(__name__)


class PythonOperator(AIFlowOperator):

    def __init__(self,
                 name: str,
                 python_callable: Callable,
                 callable_args: Optional[List] = None,
                 **kwargs):
        super().__init__(name, **kwargs)
        if not callable(python_callable):
            raise AIFlowException('`python_callable` param must be callable')
        self.python_callable = python_callable
        self.callable_args = callable_args or []
        self.process = None

    def start(self, context: Context):
        self.process = Process(target=self.python_callable, args=self.callable_args)
        self.process.start()
        logger.info('Running python process on pid: %s', self.process.pid)

    def stop(self, context: Context):
        self.process.terminate()
        self.process.join()

    def await_termination(self, context: Context, timeout: Optional[int] = None):
        self.process.join(timeout=timeout)
