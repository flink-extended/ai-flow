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

"""Workflow command"""
from typing import List

import cloudpickle
from ai_flow.metadata.workflow import WorkflowMeta

from ai_flow import ops
from ai_flow.cli.simple_table import AIFlowConsole


def upload_workflows(args):
    """Uploads the workflow by workflow name."""
    artifacts = args.files.split(',') if args.files is not None else None
    workflows = ops.upload_workflows(workflow_file_path=args.file_path,
                                     artifacts=artifacts)
    for w in workflows:
        print(f"Workflow: {w.namespace}.{w.name}, submitted.")


def list_workflow(args):
    """Lists all the workflows."""
    namespace = args.namespace if args.namespace is not None else 'default'
    workflows: List[WorkflowMeta] = []
    offset = 0
    while True:
        res = ops.list_workflows(namespace=namespace,
                                 limit=10,
                                 offset=offset)
        if res is None:
            break
        else:
            offset += len(res)
            workflows.extend(res)
    AIFlowConsole().print_as(
        data=sorted(workflows, key=lambda w: w.id),
        output=args.output,
        mapper=lambda x: {
            'id': x.id,
            'workflow_name': x.name,
            'namespace': x.namespace,
            'create_time': x.create_time,
            'update_time': x.update_time,
            'is_enabled': x.is_enabled,
            'event_offset': x.event_offset
        },
    )


def show_workflow(args):
    """Shows the workflow by workflow name."""
    namespace = args.namespace if args.namespace is not None else 'default'
    workflow = ops.get_workflow(workflow_name=args.workflow_name,
                                namespace=namespace)
    if workflow is None:
        print("No such workflow.")
    else:
        workflow_obj = cloudpickle.loads(workflow.workflow_object)
        AIFlowConsole().print_as(
            data=[workflow],
            output=args.output,
            mapper=lambda x: {
                'id': x.id,
                'workflow_name': x.name,
                'namespace': x.namespace,
                'create_time': x.create_time,
                'update_time': x.update_time,
                'is_enabled': x.is_enabled,
                'event_offset': x.event_offset,
                'content': x.content,
                'config': workflow_obj.config,
                'tasks': workflow_obj.tasks,
                'rules': workflow_obj.rules
            },
        )


def delete_workflow(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    workflow_name = args.workflow_name
    ops.delete_workflow(workflow_name=workflow_name,
                        namespace=namespace)
    print(f"Workflow: {namespace}.{workflow_name} deleted.")


def disable_workflow(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    workflow_name = args.workflow_name
    ops.disable_workflow(workflow_name=workflow_name,
                         namespace=namespace)
    print(f"Workflow: {namespace}.{workflow_name} disabled.")


def enable_workflow(args):
    namespace = args.namespace if args.namespace is not None else 'default'
    workflow_name = args.workflow_name
    ops.enable_workflow(workflow_name=workflow_name,
                        namespace=namespace)
    print(f"Workflow: {namespace}.{workflow_name} enabled.")
