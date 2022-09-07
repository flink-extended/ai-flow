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

"""Workflow trigger command"""
from typing import List

from ai_flow.metadata.workflow_event_trigger import WorkflowEventTriggerMeta

from ai_flow import ops
from ai_flow.cli.simple_table import AIFlowConsole


def delete_workflow_trigger(args):
    workflow_trigger_id = int(args.workflow_trigger_id)
    ops.delete_workflow_trigger(workflow_trigger_id)
    print(f"Workflow trigger: {workflow_trigger_id} deleted.")


def delete_workflow_triggers(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    ops.delete_workflow_triggers(workflow_name=args.workflow_name, namespace=namespace)
    print(f"All triggers of workflow: {namespace}.{args.workflow_name} deleted.")


def show_workflow_trigger(args):
    workflow_trigger = ops.get_workflow_trigger(int(args.workflow_trigger_id))
    if workflow_trigger is None:
        print("No such workflow trigger.")
    else:
        AIFlowConsole().print_as(
            data=[workflow_trigger],
            output=args.output,
            mapper=lambda x: {
                'id': x.id,
                'workflow_id': x.workflow_id,
                'rule': x.rule,
                'create_time': x.create_time,
                'is_paused': x.is_paused,
            },
        )


def list_workflow_triggers(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    workflow_name = args.workflow_name
    triggers: List[WorkflowEventTriggerMeta] = []
    offset = 0
    while True:
        res = ops.list_workflow_triggers(workflow_name=workflow_name,
                                         namespace=namespace,
                                         limit=10,
                                         offset=offset)
        if res is None:
            break
        else:
            offset += len(res)
            triggers.extend(res)
    AIFlowConsole().print_as(
        data=sorted(triggers, key=lambda e: e.id),
        output=args.output,
        mapper=lambda x: {
            'id': x.id,
            'workflow_id': x.workflow_id,
            'rule': x.rule,
            'create_time': x.create_time,
            'is_paused': x.is_paused,
        },
    )


def pause_workflow_trigger(args):
    workflow_trigger_id = int(args.workflow_trigger_id)
    ops.pause_workflow_trigger(workflow_trigger_id)
    print(f'Workflow trigger: {workflow_trigger_id} paused.')


def resume_workflow_trigger(args):
    workflow_trigger_id = int(args.workflow_trigger_id)
    ops.resume_workflow_trigger(workflow_trigger_id)
    print(f'Workflow trigger: {workflow_trigger_id} resumed.')
