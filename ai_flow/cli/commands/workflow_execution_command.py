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

"""Workflow execution command"""
from typing import List

from ai_flow.metadata.workflow_execution import WorkflowExecutionMeta

from ai_flow import ops
from ai_flow.cli.simple_table import AIFlowConsole


def start_workflow_execution(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    workflow_name = args.workflow_name
    execution_id = ops.start_workflow_execution(workflow_name=workflow_name, namespace=namespace)
    print(f"Workflow execution: {execution_id} submitted.")


def stop_workflow_execution(args):
    workflow_execution_id = int(args.workflow_execution_id)
    ops.stop_workflow_execution(workflow_execution_id)
    print(f'Stopping workflow execution: {workflow_execution_id}')


def stop_workflow_executions(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    workflow_name = args.workflow_name
    ops.stop_workflow_executions(workflow_name=workflow_name,
                                 namespace=namespace)
    print(f'Stopping all workflow executions of workflow: {namespace}.{workflow_name}')


def show_workflow_execution(args):
    workflow_execution = ops.get_workflow_execution(int(args.workflow_execution_id))
    if workflow_execution is None:
        print("No such workflow execution.")
    else:
        AIFlowConsole().print_as(
            data=[workflow_execution],
            output=args.output,
            mapper=lambda x: {
                'id': x.id,
                'workflow_id': x.workflow_id,
                'begin_date': x.begin_date,
                'end_date': x.end_date,
                'status': x.status,
                'run_type': x.run_type,
                'snapshot_id': x.snapshot_id,
                'event_offset': x.event_offset,
            },
        )


def list_workflow_executions(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    workflow_name = args.workflow_name
    executions: List[WorkflowExecutionMeta] = []
    offset = 0
    while True:
        res = ops.list_workflow_executions(workflow_name=workflow_name,
                                           namespace=namespace,
                                           limit=10,
                                           offset=offset)
        if res is None:
            break
        else:
            offset += len(res)
            executions.extend(res)
    AIFlowConsole().print_as(
        data=sorted(executions, key=lambda e: e.id),
        output=args.output,
        mapper=lambda x: {
            'id': x.id,
            'workflow_id': x.workflow_id,
            'begin_date': x.begin_date,
            'end_date': x.end_date,
            'status': x.status,
            'run_type': x.run_type,
            'snapshot_id': x.snapshot_id,
            'event_offset': x.event_offset,
        },
    )


def delete_workflow_execution(args):
    workflow_execution_id = int(args.workflow_execution_id)
    ops.delete_workflow_execution(workflow_execution_id)
    print(f'Workflow execution: {workflow_execution_id} deleted.')

