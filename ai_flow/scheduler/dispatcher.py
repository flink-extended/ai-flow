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
import json
import logging

from notification_service.model.event import Event
from typing import List

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.db_util.session import create_session
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.model.internal.events import AIFlowEventType, SchedulingEventType, EventContextConstant
from ai_flow.scheduler.rule_extractor import RuleExtractor
from ai_flow.scheduler.worker import Worker


class Dispatcher(object):
    """
    Dispatcher generates scheduling units based on events and distributes them to specified workers for processing.
    """

    def __init__(self,
                 workers: List[Worker]):
        self.workers = workers
        self.worker_num = len(workers)
        self.rule_extractor = RuleExtractor()
        self.max_committed_offset = self._get_max_committed_offset()

    @staticmethod
    def _is_scheduling_event(event: Event) -> bool:
        if AIFlowEventType.AIFLOW_SCHEDULING_EVENT == event.key:
            return True
        else:
            return False

    def _worker_index(self, value: int) -> int:
        return value % self.worker_num

    @staticmethod
    def _get_max_committed_offset():
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_offset = metadata_manager.get_max_event_offset_of_workflow()
            workflow_offset = workflow_offset if workflow_offset is not None else -1
            workflow_execution_offset = metadata_manager.get_max_event_offset_of_workflow_execution()
            workflow_execution_offset = workflow_execution_offset if workflow_execution_offset is not None else -1
            return max(workflow_offset, workflow_execution_offset)

    def _in_recovery(self, event: Event):
        return event.offset <= self.max_committed_offset

    @staticmethod
    def _get_committed_offset_of_workflow_execution(workflow_execution_id):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            we = metadata_manager.get_workflow_execution(workflow_execution_id)
            if not we:
                raise AIFlowException(f'Workflow execution with id {workflow_execution_id} not exists')
            return we.event_offset

    def _has_processed_by_workflow(self, event, workflow_id) -> bool:
        if self._in_recovery(event):
            with create_session() as session:
                metadata_manager = MetadataManager(session)
                workflow = metadata_manager.get_workflow_by_id(workflow_id)
                if not workflow:
                    logging.warning(f'Workflow with id {workflow_id} not exists, skip processing event: {event}')
                    return True
                if event.offset <= workflow.event_offset:
                    logging.debug(f"Event {event} has been processed by workflow {workflow_id}")
                    return True
        return False

    def _has_processed_by_workflow_execution(self, event, workflow_execution_id) -> bool:
        if self._in_recovery(event):
            with create_session() as session:
                metadata_manager = MetadataManager(session)
                we = metadata_manager.get_workflow_execution(workflow_execution_id)
                if not we:
                    logging.warning(f'Workflow execution with id {workflow_execution_id} not exists, '
                                    f'skip processing event: {event}')
                    return True
                if event.offset <= we.event_offset:
                    logging.debug(f"Event {event} has been processed by workflow execution {workflow_execution_id}")
                    return True
        return False

    def dispatch(self, event: Event):
        is_scheduling_event = self._is_scheduling_event(event=event)
        if is_scheduling_event:
            context = json.loads(event.context)
            if SchedulingEventType.START_WORKFLOW_EXECUTION == SchedulingEventType(event.value) or \
                    SchedulingEventType.PERIODIC_RUN_WORKFLOW == SchedulingEventType(event.value):
                workflow_id = context[EventContextConstant.WORKFLOW_ID]
                if self._has_processed_by_workflow(event, workflow_id):
                    return
                worker_index = self._worker_index(workflow_id)
            else:
                workflow_execution_id = context[EventContextConstant.WORKFLOW_EXECUTION_ID]
                if self._has_processed_by_workflow_execution(event, workflow_execution_id):
                    return
                worker_index = self._worker_index(workflow_execution_id)

            self.workers[worker_index].add_unit((event, None))
        else:
            workflow_rules = self.rule_extractor.extract_workflow_rules(event=event)
            for rule in workflow_rules:
                if self._has_processed_by_workflow(event, rule.workflow_id):
                    continue
                worker_index = self._worker_index(rule.workflow_id)
                self.workers[worker_index].add_unit((event, rule))

            workflow_execution_rules = self.rule_extractor.extract_workflow_execution_rules(event=event)
            for rule in workflow_execution_rules:
                if self._has_processed_by_workflow_execution(event, rule.workflow_execution_id):
                    continue
                worker_index = self._worker_index(rule.workflow_execution_id)
                self.workers[worker_index].add_unit((event, rule))
