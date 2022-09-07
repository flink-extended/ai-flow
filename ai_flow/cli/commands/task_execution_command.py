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

"""Task execution command"""
from typing import List

from ai_flow.metadata.task_execution import TaskExecutionMeta

from ai_flow import ops
from ai_flow.cli.simple_table import AIFlowConsole


def start_task_execution(args):
    workflow_execution_id = int(args.workflow_execution_id)
    task_name = args.task_name
    key = ops.start_task_execution(workflow_execution_id=workflow_execution_id, task_name=task_name)
    print(f"Task execution: {key} submitted.")


def stop_task_execution(args):
    workflow_execution_id = int(args.workflow_execution_id)
    task_name = args.task_name
    ops.stop_task_execution(workflow_execution_id=workflow_execution_id, task_name=task_name)
    print(f"Stopping execution of task: {task_name} of workflow execution: {workflow_execution_id}.")


def show_task_execution(args):
    task_execution = ops.get_task_execution(int(args.task_execution_id))
    if task_execution is None:
        print('No such workflow execution.')
    else:
        AIFlowConsole().print_as(
            data=[task_execution],
            output=args.output,
            mapper=lambda x: {
                'id': x.id,
                'workflow_execution_id': x.workflow_execution_id,
                'task_name': x.task_name,
                'sequence_number': x.sequence_number,
                'try_number': x.try_number,
                'begin_date': x.begin_date,
                'end_date': x.end_date,
                'status': x.status,
            },
        )


def list_task_executions(args):
    executions: List[TaskExecutionMeta] = []
    offset = 0
    while True:
        res = ops.list_task_executions(workflow_execution_id=int(args.workflow_execution_id),
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
            'workflow_execution_id': x.workflow_execution_id,
            'task_name': x.task_name,
            'sequence_number': x.sequence_number,
            'try_number': x.try_number,
            'begin_date': x.begin_date,
            'end_date': x.end_date,
            'status': x.status,
        },
    )
