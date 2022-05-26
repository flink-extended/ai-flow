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
import cloudpickle
from copy import deepcopy
from typing import List, Dict, Set, Tuple

from notification_service.event import Event, EventKey

from ai_flow.metadata.metadata_manager import MetadataManager, Filters, FilterEqual
from ai_flow.metadata.workflow_event_trigger import WorkflowEventTriggerMeta
from ai_flow.model.internal.conditions import match_events
from ai_flow.model.internal.events import EventContextConstant
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.status import WorkflowStatus
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.rule_wrapper import TaskRuleWrapper, WorkflowExecutionRuleWrapper, WorkflowRuleWrapper

# It represents an EventKey. Its format is (namespace, name, event_type, sender).
EventTuple = Tuple[str, str, str, str]


def parse_workflow_execution_id(context):
    """Parse the workflow execution id from the context"""
    if context is not None:
        context_dict = json.loads(context)
        if EventContextConstant.WORKFLOW_EXECUTION_ID in context_dict:
            return context_dict[EventContextConstant.WORKFLOW_EXECUTION_ID]
    return None


def gen_all_combination(inputs: list) -> list:
    """Get all combinations of a list"""
    if len(inputs) == 1:
        if inputs[0] is None:
            return [(None,)]
        else:
            return [(inputs[0],), (None,)]
    results = gen_all_combination(inputs[1:])
    new_results = []
    for result in results:
        if inputs[0] is not None:
            r1 = deepcopy(result)
            r1 = (inputs[0],) + r1
            new_results.append(r1)
        r2 = deepcopy(result)
        r2 = (None,) + r2
        new_results.append(r2)
    return new_results


def gen_all_tuple_by_event_key(event_key: EventKey) -> List[EventTuple]:
    """Generate all tuple combinations that match the event key"""
    keys = [event_key.namespace, event_key.name, event_key.event_type, event_key.sender]
    return gen_all_combination(keys)


def expect_keys_to_tuple_set(expect_keys: List[EventKey]) -> Set[EventTuple]:
    r = set()
    for expect_key in expect_keys:
        r.add((expect_key.namespace, expect_key.name, expect_key.event_type, expect_key.sender))
    return r


def workflow_expect_event_tuples(workflow: Workflow) -> Set[EventTuple]:
    """Get the event tuples contained in a workflow"""
    result_keys = set()
    for task_name, rules in workflow.rules.items():
        for rule in rules:
            keys = expect_keys_to_tuple_set(rule.condition.expect_events)
            result_keys = result_keys | keys
    return result_keys


def build_task_rule_index(workflow_dict: Dict[int, Workflow]) -> Dict[EventTuple, Set[int]]:
    """Build the workflow index by task rules"""
    task_rule_index = {}
    for workflow_id, workflow in workflow_dict.items():
        expect_keys = workflow_expect_event_tuples(workflow=workflow)
        for key in expect_keys:
            if key not in task_rule_index:
                task_rule_index[key] = set()
            task_rule_index[key].add(workflow_id)
    return task_rule_index


def build_workflow_rule_index(workflow_trigger_list: List[WorkflowEventTriggerMeta]) -> Dict[EventTuple, Set[int]]:
    """Build the workflow index by workflow rules"""
    workflow_rule_index = {}
    for workflow_trigger_meta in workflow_trigger_list:
        rule: WorkflowRule = cloudpickle.loads(workflow_trigger_meta.rule)
        expect_keys = expect_keys_to_tuple_set(rule.condition.expect_events)
        for key in expect_keys:
            if key not in workflow_rule_index:
                workflow_rule_index[key] = set()
            workflow_rule_index[key].add(workflow_trigger_meta.workflow_id)
    return workflow_rule_index


class RuleIndex(object):
    """Stores the index that the event triggers the workflow"""
    def __init__(self,
                 workflow_dict: Dict[int, Workflow],
                 workflow_trigger_list: List[WorkflowEventTriggerMeta]):
        self.task_rule_index: Dict[EventTuple, Set[int]] \
            = build_task_rule_index(workflow_dict=workflow_dict)
        self.workflow_rule_index: Dict[EventTuple, Set[int]] \
            = build_workflow_rule_index(workflow_trigger_list=workflow_trigger_list)

    def affected_workflows_by_task_rule(self, event: Event) -> Set[int]:
        keys = gen_all_tuple_by_event_key(event.event_key)
        result_set = set()
        for key in keys:
            if key in self.task_rule_index:
                result_set = result_set | self.task_rule_index[key]
        return result_set

    def affected_workflows_by_workflow_rule(self, event: Event) -> Set[int]:
        keys = gen_all_tuple_by_event_key(event.event_key)
        result_set = set()
        for key in keys:
            if key in self.workflow_rule_index:
                result_set = result_set | self.workflow_rule_index[key]
        return result_set


def extract_task_rules_from_workflow_by_event(event, workflow) \
        -> List[TaskRuleWrapper]:
    """Get the task rules of a workflow based on the event"""
    task_rule_wrapper_list = []
    for task_name, rules in workflow.rules.items():
        rule_list = []
        for rule in rules:
            if match_events(event_keys=rule.condition.expect_events, event=event):
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
    def __init__(self, metadata_manager: MetadataManager):
        self.metadata_manager = metadata_manager
        self.workflow_dict: Dict[int, Workflow] = self._load_workflows()
        self.workflow_trigger_list: List[WorkflowEventTriggerMeta] = self._load_workflow_triggers()
        self.event_workflow_index: RuleIndex \
            = RuleIndex(workflow_dict=self.workflow_dict,
                        workflow_trigger_list=self.workflow_trigger_list)

    def _load_workflows(self):
        workflows = self.metadata_manager.list_workflows(namespace=None, page_size=None)
        workflow_dict = {}
        for w_m in workflows:
            workflow_dict[w_m.id] = cloudpickle.loads(w_m.workflow_object)
        return workflow_dict

    def _load_workflow_triggers(self):
        return self.metadata_manager.list_all_workflow_triggers()

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
                    workflow_executions = self.metadata_manager.list_workflow_executions(
                        workflow_id=workflow_id,
                        page_size=None,
                        filters=Filters(filters=[(FilterEqual('status'), WorkflowStatus.RUNNING.value)]))
                    for workflow_execution in workflow_executions:
                        results.append(WorkflowExecutionRuleWrapper(workflow_execution_id=workflow_execution.id,
                                                                    task_rule_wrappers=task_rule_list))
            return results
        else:
            workflow_execution = self.metadata_manager.get_workflow_execution(
                workflow_execution_id=workflow_execution_id)
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
        for workflow_id in workflow_id_list:
            rules = []
            metas = self.metadata_manager.list_workflow_triggers(workflow_id=workflow_id)
            for meta in metas:
                rule = cloudpickle.loads(meta.rule)
                if match_events(rule.condition.expect_events, event):
                    rules.append(cloudpickle.loads(meta.rule))
            if len(rules) > 0:
                results.append(WorkflowRuleWrapper(workflow_id=workflow_id, rules=rules))
        return results
