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
import queue
import threading

from ai_flow.scheduler.scheduling_unit import SchedulingUnit


class Worker(threading.Thread):

    def __init__(self,
                 max_queue_size: int = 20,
                 task_executor=None):
        super().__init__()
        self.input_queue = queue.Queue(max_queue_size)
        self.task_executor = task_executor

    def add_unit(self, unit: SchedulingUnit):
        self.input_queue.put(unit)

    def run(self) -> None:
        pass
