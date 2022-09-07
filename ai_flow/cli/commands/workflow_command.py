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
import os
import sys

from ai_flow.api.workflow_operation import delete_workflow, get_workflow, get_workflow_execution, list_workflows, \
    list_workflow_executions, pause_workflow_scheduling, resume_workflow_scheduling, start_new_workflow_execution, \
    stop_all_workflow_executions, stop_workflow_execution, submit_workflow
from ai_flow.cli.simple_table import AIFlowConsole
from ai_flow.common.module_load import load_module
from ai_flow.util.cli_utils import init_config
from ai_flow.util.time_utils import parse_date


@init_config
def workflow_delete(args):
    """Deletes all DB records related to the specified workflow."""
    if (
            args.yes
            or input('This will drop all existing records related to the specified workflow. Proceed? (y/n)').upper()
            == 'Y'
    ):
        workflow = delete_workflow(workflow_name=args.workflow_name)
        print("Workflow: {}, deleted: {}.".format(args.workflow_name, workflow is not None))
    else:
        print('Cancelled')


@init_config
def workflow_list(args):
    """Lists all the workflows."""
    workflows = list_workflows(sys.maxsize, 0)
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


@init_config
def workflow_list_executions(args):
    """Lists all workflow executions of the workflow by workflow name."""
    workflow_executions = list_workflow_executions(args.workflow_name)
    AIFlowConsole().print_as(
        data=sorted(workflow_executions, key=lambda w: w.workflow_execution_id),
        output=args.output,
        mapper=lambda x: {
            'workflow_execution_id': x.workflow_execution_id,
            'workflow_name': x.workflow_info.workflow_name,
            'status': x.status,
            'properties': x.properties,
            'start_date': parse_date(x.start_date),
            'end_date': parse_date(x.end_date),
            'context': x.context
        },
    )


@init_config
def workflow_pause_scheduling(args):
    """Pauses a workflow scheduling."""
    workflow = pause_workflow_scheduling(args.workflow_name)
    print("Workflow: {}, paused: {}.".format(args.workflow_name, workflow is not None))


@init_config
def workflow_resume_scheduling(args):
    """Resumes a paused workflow scheduling."""
    workflow = resume_workflow_scheduling(args.workflow_name)
    print("Workflow: {}, resumed: {}.".format(args.workflow_name, workflow is not None))


@init_config
def workflow_show(args):
    """Shows the workflow by workflow name."""
    workflow = get_workflow(args.workflow_name)
    AIFlowConsole().print_as(
        data=[workflow],
        output=args.output,
        mapper=lambda x: {
            'namespace': x.namespace,
            'workflow_name': x.workflow_name,
            'properties': x.properties,
            'scheduling_rules': x.scheduling_rules
        },
    )


@init_config
def workflow_show_execution(args):
    """Shows the workflow execution by workflow execution id."""
    workflow_execution = get_workflow_execution(args.workflow_execution_id)
    AIFlowConsole().print_as(
        data=[workflow_execution],
        output=args.output,
        mapper=lambda x: {
            'workflow_execution_id': x.workflow_execution_id,
            'workflow_name': x.workflow_info.workflow_name,
            'status': x.status,
            'properties': x.properties,
            'start_date': parse_date(x.start_date),
            'end_date': parse_date(x.end_date),
            'context': x.context
        },
    )


@init_config
def workflow_start_execution(args):
    """Starts a new workflow execution by workflow name."""
    workflow_execution = start_new_workflow_execution(args.workflow_name, args.context)
    print("Workflow: {}, started: {}.".format(args.workflow_name, workflow_execution is not None))


@init_config
def workflow_stop_execution(args):
    """Stops the workflow execution by workflow execution id."""
    workflow_execution = stop_workflow_execution(args.workflow_execution_id)
    print("Workflow Execution: {}, stopped: {}.".format(args.workflow_execution_id, workflow_execution is not None))


@init_config
def workflow_stop_executions(args):
    """Stops all workflow executions by workflow name."""
    workflow_executions = stop_all_workflow_executions(args.workflow_name)
    print("Workflow: {}, stopped: {}.".format(args.workflow_name, str(len(workflow_executions) > 0)))


@init_config
def workflow_submit(args):
    """Submits the workflow by workflow name."""
    dependencies_path = os.path.join(args.project_path, 'dependencies', 'python')
    if os.path.exists(dependencies_path):
        sys.path.insert(0, dependencies_path)
    workflow_path = os.path.join(args.project_path, 'workflows', args.workflow_name)
    sys.path.insert(0, workflow_path)
    workflow_file_path = os.path.join(args.project_path,
                                      'workflows',
                                      args.workflow_name,
                                      '{}.py'.format(args.workflow_name))
    load_module(workflow_file_path)
    workflow = submit_workflow(args.workflow_name)
    print("Workflow: {}, submitted: {}.".format(args.workflow_name, workflow is not None))
