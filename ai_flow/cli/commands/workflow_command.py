# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# 'License'); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Workflow command"""
import sys

import cloudpickle
from ai_flow.cli.simple_table import AIFlowConsole
from ai_flow.sdk import operation


def workflow_list(args):
    """Lists all the workflows."""
    workflows = operation.list_workflows(sys.maxsize, 0)
    AIFlowConsole().print_as(
        data=sorted(workflows, key=lambda w: w.workflow_name),
        output=args.output,
        mapper=lambda x: {
            'namespace': x.namespace,
            'workflow_name': x.workflow_name,
            'properties': x.properties,
            'scheduling_rules': x.scheduling_rules
        },
    )


def workflow_show(args):
    """Shows the workflow by workflow name."""
    workflow = operation.get_workflow(args.namespace, args.workflow_name)
    if workflow is None:
        print("No such workflow.")
    else:
        workflow_obj = cloudpickle.loads(workflow.workflow_object)
        AIFlowConsole().print_as(
            data=[workflow],
            output=args.output,
            mapper=lambda x: {
                'namespace': x.namespace,
                'workflow_name': x.workflow_name,
                'content': x.content,
                'config': workflow_obj.config,
                'tasks': workflow_obj.tasks,
                'rules': workflow_obj.rules
            },
        )


def workflow_upload(args):
    """Uploads the workflow by workflow name."""
    namespace = args.namespace if args.namespace is not None else 'default'
    artifacts = args.files.split(',') if args.files is not None else None
    workflows = operation.upload_workflows(workflow_file_path=args.file_path,
                                           artifacts=artifacts)
    for w in workflows:
        print("Workflow: {}, submitted.".format(w.name))
