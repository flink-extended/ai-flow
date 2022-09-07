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
import threading

import cloudpickle
from typing import List, Dict, Set, Tuple

from notification_service.model.event import Event

from ai_flow.common.util.db_util.session import create_session
from ai_flow.common.util.json_utils import is_valid_json
from ai_flow.metadata.metadata_manager import MetadataManager, Filters, FilterEqual
from ai_flow.metadata.workflow_event_trigger import WorkflowEventTriggerMeta
from ai_flow.model.internal.conditions import match_events
from ai_flow.model.internal.events import EventContextConstant
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.status import WorkflowStatus
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.rule_wrapper import TaskRuleWrapper, WorkflowExecutionRuleWrapper, WorkflowRuleWrapper

# It represents an event key. Its format is (namespace, key).
EventKeyTuple = Tuple[str, str]


def parse_workflow_execution_id(context):
    """Parse the workflow execution id from the context"""
    if context is not None and is_valid_json(context):
        context_dict = json.loads(context)
        if EventContextConstant.WORKFLOW_EXECUTION_ID in context_dict:
            return context_dict[EventContextConstant.WORKFLOW_EXECUTION_ID]
    return None


def expect_keys_to_tuple_set(namespace: str, expect_keys: List[str]) -> Set[EventKeyTuple]:
    r = set()
    for key in expect_keys:
        r.add((namespace, key))
    return r


def workflow_expect_event_tuples(workflow: Workflow) -> Set[EventKeyTuple]:
    """Get the event tuples contained in a workflow"""
    result_keys = set()
    for task_name, rules in workflow.rules.items():
        for rule in rules:
            keys = expect_keys_to_tuple_set(workflow.namespace, rule.condition.expect_event_keys)
            result_keys = result_keys | keys
    return result_keys


def append_task_rule_index(task_rule_index: Dict[EventKeyTuple, Set[int]], workflow: Workflow, workflow_id: int):
    expect_keys = workflow_expect_event_tuples(workflow=workflow)
    for key in expect_keys:
        if key not in task_rule_index:
            task_rule_index[key] = set()
        task_rule_index[key].add(workflow_id)


def build_task_rule_index(workflow_dict: Dict[int, Workflow]) -> Dict[EventKeyTuple, Set[int]]:
    """Build the workflow index by task rules"""
    task_rule_index = {}
    for workflow_id, workflow in workflow_dict.items():
        append_task_rule_index(task_rule_index, workflow, workflow_id)
    return task_rule_index


def build_workflow_rule_index(workflow_dict: Dict[int, Workflow],
                              workflow_trigger_dict: Dict[int, WorkflowEventTriggerMeta]
                              ) -> Dict[EventKeyTuple, Set[int]]:
    """Build the workflow index by workflow rules"""
    workflow_rule_index = {}
    for workflow_trigger_meta in workflow_trigger_dict.values():
        if workflow_trigger_meta.workflow_id not in workflow_dict:
            continue
        try:
            workflow: Workflow = workflow_dict.get(workflow_trigger_meta.workflow_id)
            rule: WorkflowRule = cloudpickle.loads(workflow_trigger_meta.rule)

            expect_keys = expect_keys_to_tuple_set(workflow.namespace, rule.condition.expect_event_keys)
            for key in expect_keys:
                if key not in workflow_rule_index:
                    workflow_rule_index[key] = set()
                workflow_rule_index[key].add(workflow_trigger_meta.workflow_id)
        except Exception as e:
            logging.exception("Failed to load workflow trigger: %s, %s", workflow_trigger_meta.id, e)
    return workflow_rule_index


class RuleIndex(object):
    """Stores the index that the event triggers the workflow"""
    def __init__(self,
                 workflow_dict: Dict[int, Workflow],
                 workflow_trigger_dict: Dict[int, WorkflowEventTriggerMeta]):
        self.task_rule_index: Dict[EventKeyTuple, Set[int]] \
            = build_task_rule_index(workflow_dict=workflow_dict)
        self.workflow_rule_index: Dict[EventKeyTuple, Set[int]] \
            = build_workflow_rule_index(workflow_dict=workflow_dict,
                                        workflow_trigger_dict=workflow_trigger_dict)

    def affected_workflows_by_task_rule(self, event: Event) -> Set[int]:
        key_tuple: EventKeyTuple = (event.namespace, event.key)
        if key_tuple in self.task_rule_index:
            return self.task_rule_index[key_tuple]
        else:
            return set()

    def affected_workflows_by_workflow_rule(self, event: Event) -> Set[int]:
        key_tuple: EventKeyTuple = (event.namespace, event.key)
        if key_tuple in self.workflow_rule_index:
            return self.workflow_rule_index[key_tuple]
        else:
            return set()


def extract_task_rules_from_workflow_by_event(event, workflow) \
        -> List[TaskRuleWrapper]:
    """Get the task rules of a workflow based on the event"""
    task_rule_wrapper_list = []
    for task_name, rules in workflow.rules.items():
        rule_list = []
        for rule in rules:
            if match_events(event_keys=rule.condition.expect_event_keys, event=event):
                rule_list.append(rule)
        if len(rule_list) > 0:
            rule_wrapper = TaskRuleWrapper(task_name=task_name,
                                           rules=rule_list)
            task_rule_wrapper_list.append(rule_wrapper)
    return task_rule_wrapper_list


class RuleExtractor(object):
    """
    RuleExtractor extracts the Rule to be executed according to the event and workflow information.
    It contains two types of rules:
    1. Rules for workflow.
    2. Rules for workflow execution.
    """
    def __init__(self):
        self.workflow_dict: Dict[int, Workflow] = self._load_workflows()
        self.workflow_trigger_dict: Dict[int, WorkflowEventTriggerMeta] = self._load_workflow_triggers()
        self.event_workflow_index: RuleIndex = self._load_rule_index()
        self._lock = threading.RLock()

    @staticmethod
    def _load_workflows():
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflows = metadata_manager.list_workflows(
                namespace=None, filters=Filters(filters=[(FilterEqual('is_enabled'), True)]))
        workflow_dict = {}
        for w_m in workflows:
            try:
                workflow_dict[w_m.id] = cloudpickle.loads(w_m.workflow_object)
            except Exception as e:
                logging.exception("Failed to load workflow: %s, %s", w_m.name, e)
        return workflow_dict

    @staticmethod
    def _load_workflow_triggers():
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_triggers = metadata_manager.list_all_workflow_triggers(
                filters=Filters(filters=[(FilterEqual('is_paused'), False)]))
        trigger_dict = {}
        for w_t in workflow_triggers:
            trigger_dict[w_t.id] = w_t
        return trigger_dict

    def _load_rule_index(self):
        return RuleIndex(workflow_dict=self.workflow_dict,
                         workflow_trigger_dict=self.workflow_trigger_dict)

    def update_workflow(self, workflow_id, pickled_workflow):
        with self._lock:
            self.workflow_dict[workflow_id] = cloudpickle.loads(pickled_workflow)
            self.event_workflow_index = self._load_rule_index()

    def delete_workflow(self, workflow_id):
        with self._lock:
            if workflow_id in self.workflow_dict:
                self.workflow_dict.pop(workflow_id)
                self.event_workflow_index = self._load_rule_index()

    def update_workflow_trigger(self, trigger: WorkflowEventTriggerMeta):
        with self._lock:
            self.workflow_trigger_dict[trigger.id] = trigger
            self.event_workflow_index.workflow_rule_index = build_workflow_rule_index(
                self.workflow_dict, self.workflow_trigger_dict)

    def delete_workflow_trigger(self, trigger_id):
        with self._lock:
            self.workflow_trigger_dict.pop(trigger_id)
            self.event_workflow_index.workflow_rule_index = build_workflow_rule_index(
                self.workflow_dict, self.workflow_trigger_dict)

    def extract_workflow_execution_rules(self, event: Event) -> List[WorkflowExecutionRuleWrapper]:
        """Extract rules for workflow execution"""
        workflow_execution_id = parse_workflow_execution_id(event.context)
        if workflow_execution_id is None:
            workflow_id_list = self.event_workflow_index.affected_workflows_by_task_rule(event=event)
            results = []
            for workflow_id in workflow_id_list:
                workflow = self.workflow_dict[workflow_id]
                task_rule_list = extract_task_rules_from_workflow_by_event(event=event, workflow=workflow)
                if len(task_rule_list) > 0:
                    with create_session() as session:
                        metadata_manager = MetadataManager(session)
                        workflow_executions = metadata_manager.list_workflow_executions(
                            workflow_id=workflow_id,
                            page_size=None,
                            filters=Filters(filters=[(FilterEqual('status'), WorkflowStatus.RUNNING.value)]))
                    for workflow_execution in workflow_executions:
                        results.append(WorkflowExecutionRuleWrapper(workflow_execution_id=workflow_execution.id,
                                                                    task_rule_wrappers=task_rule_list))
            return results
        else:
            with create_session() as session:
                metadata_manager = MetadataManager(session)
                workflow_execution = metadata_manager.get_workflow_execution(
                    workflow_execution_id=workflow_execution_id)
            if not workflow_execution:
                logging.warning(f'Workflow execution {workflow_execution_id} not exists.')
                return []
            workflow = self.workflow_dict[workflow_execution.workflow_id]
            task_rule_list = extract_task_rules_from_workflow_by_event(event=event, workflow=workflow)

            workflow_execution_rule_wrapper = WorkflowExecutionRuleWrapper(workflow_execution_id=workflow_execution_id,
                                                                           task_rule_wrappers=task_rule_list)
            if workflow_execution_rule_wrapper is not None:
                return [workflow_execution_rule_wrapper]
            else:
                return []

    def extract_workflow_rules(self, event: Event) -> List[WorkflowRuleWrapper]:
        """Extract rules for workflow"""
        results = []
        workflow_id_list = self.event_workflow_index.affected_workflows_by_workflow_rule(event=event)
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            for workflow_id in workflow_id_list:
                rules = []
                metas = metadata_manager.list_workflow_triggers(workflow_id=workflow_id)
                for meta in metas:
                    rule = cloudpickle.loads(meta.rule)
                    if match_events(rule.condition.expect_event_keys, event):
                        rules.append(cloudpickle.loads(meta.rule))
                if len(rules) > 0:
                    results.append(WorkflowRuleWrapper(workflow_id=workflow_id, rules=rules))
        return results

