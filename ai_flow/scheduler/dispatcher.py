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
import json
from notification_service.event import Event
from typing import List

from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.model.internal.events import AIFlowEventType, SchedulingEventType, EventContextConstant
from ai_flow.scheduler.rule_extractor import RuleExtractor
from ai_flow.scheduler.worker import Worker


class Dispatcher(object):

    def __init__(self,
                 workers: List[Worker],
                 metadata_manager: MetadataManager):
        self.workers = workers
        self.worker_num = len(workers)
        self.rule_extractor = RuleExtractor(metadata_manager=metadata_manager)

    @staticmethod
    def _is_scheduling_event(event: Event) -> bool:
        if AIFlowEventType.AIFLOW_SCHEDULING_EVENT == event.event_key.event_type:
            return True
        else:
            return False

    def _worker_index(self, value: int) -> int:
        return value % self.worker_num

    def dispatch(self, event: Event):
        is_scheduling_event = self._is_scheduling_event(event=event)
        if is_scheduling_event:
            context = json.loads(event.context)
            if SchedulingEventType.START_WORKFLOW_EXECUTION == SchedulingEventType(event.event_key.name):
                worker_index = self._worker_index(context[EventContextConstant.WORKFLOW_ID])
            else:
                worker_index = self._worker_index(context[EventContextConstant.WORKFLOW_EXECUTION_ID])

            self.workers[worker_index].add_unit((event, None))
        else:
            workflow_rules = self.rule_extractor.extract_workflow_rules(event=event)
            for rule in workflow_rules:
                worker_index = self._worker_index(rule.workflow_id)
                self.workers[worker_index].add_unit((event, rule))

            workflow_execution_rules = self.rule_extractor.extract_workflow_execution_rules(event=event)
            for rule in workflow_execution_rules:
                worker_index = self._worker_index(rule.workflow_execution_id)
                self.workers[worker_index].add_unit((event, rule))
