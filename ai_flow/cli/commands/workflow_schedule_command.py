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

"""Workflow schedule command"""
from typing import List

from ai_flow.metadata.workflow_schedule import WorkflowScheduleMeta

from ai_flow import ops
from ai_flow.cli.simple_table import AIFlowConsole


def add_workflow_schedule(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    schedule = ops.add_workflow_schedule(expression=args.expression,
                                         workflow_name=args.workflow_name,
                                         namespace=namespace)
    print(f"Workflow schedule: {schedule.id} created.")


def delete_workflow_schedule(args):
    workflow_schedule_id = int(args.workflow_schedule_id)
    ops.delete_workflow_schedule(workflow_schedule_id)
    print(f"Workflow schedule: {workflow_schedule_id} deleted.")


def delete_workflow_schedules(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    ops.delete_workflow_schedules(workflow_name=args.workflow_name, namespace=namespace)
    print(f"All schedules of workflow: {namespace}.{args.workflow_name} deleted.")


def show_workflow_schedule(args):
    workflow_schedule_id = int(args.workflow_schedule_id)
    workflow_schedule = ops.get_workflow_schedule(workflow_schedule_id)
    if workflow_schedule is None:
        print("No such workflow schedule.")
    else:
        AIFlowConsole().print_as(
            data=[workflow_schedule],
            output=args.output,
            mapper=lambda x: {
                'id': x.id,
                'workflow_id': x.workflow_id,
                'expression': x.expression,
                'create_time': x.create_time,
                'is_paused': x.is_paused,
            },
        )


def list_workflow_schedules(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    workflow_name = args.workflow_name
    schedules: List[WorkflowScheduleMeta] = []
    offset = 0
    while True:
        res = ops.list_workflow_schedules(workflow_name=workflow_name,
                                          namespace=namespace,
                                          limit=10,
                                          offset=offset)
        if res is None:
            break
        else:
            offset += len(res)
            schedules.extend(res)
    AIFlowConsole().print_as(
        data=sorted(schedules, key=lambda e: e.id),
        output=args.output,
        mapper=lambda x: {
            'id': x.id,
            'workflow_id': x.workflow_id,
            'expression': x.expression,
            'create_time': x.create_time,
            'is_paused': x.is_paused,
        },
    )


def pause_workflow_schedule(args):
    workflow_schedule_id = int(args.workflow_schedule_id)
    ops.pause_workflow_schedule(workflow_schedule_id)
    print(f'Workflow schedule: {workflow_schedule_id} paused.')


def resume_workflow_schedule(args):
    workflow_schedule_id = int(args.workflow_schedule_id)
    ops.resume_workflow_schedule(workflow_schedule_id)
    print(f'Workflow schedule: {workflow_schedule_id} resumed.')
