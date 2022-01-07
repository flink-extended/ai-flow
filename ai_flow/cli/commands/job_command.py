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

"""Job command"""

from ai_flow.api.workflow_operation import list_job_executions, restart_job_execution, get_job_executions, \
    start_job_execution, stop_job_execution, stop_scheduling_job, resume_scheduling_job
from ai_flow.cli.simple_table import AIFlowConsole
from ai_flow.util.cli_utils import init_config
from ai_flow.util.time_utils import parse_date


@init_config
def job_list_executions(args):
    """Lists all job executions of the workflow execution by workflow execution id."""
    job_executions = list_job_executions(args.workflow_execution_id)
    AIFlowConsole().print_as(
        data=sorted(job_executions, key=lambda j: j.job_execution_id),
        output=args.output,
        mapper=lambda x: {
            'job_execution_id': x.job_execution_id,
            'job_name': x.job_name,
            'workflow_execution_id': x.workflow_execution.workflow_execution_id,
            'status': x.status,
            'properties': x.properties,
            'start_date': parse_date(x.start_date),
            'end_date': parse_date(x.end_date),
            'execution_label': x.execution_label
        },
    )


@init_config
def job_restart_execution(args):
    """Restarts the job execution by job name and workflow execution id."""
    job_execution = restart_job_execution(args.job_name, args.workflow_execution_id)
    print("Job: {}, workflow execution: {}, restarted: {}.".format(args.job_name, args.workflow_execution_id,
                                                                   job_execution is not None))


@init_config
def job_show_execution(args):
    """Shows the job execution by job name and workflow execution id."""
    job_executions = get_job_executions(args.job_name, args.workflow_execution_id)
    AIFlowConsole().print_as(
        data=sorted(job_executions, key=lambda j: j.job_execution_id),
        output=args.output,
        mapper=lambda x: {
            'job_execution_id': x.job_execution_id,
            'job_name': x.job_name,
            'workflow_execution_id': x.workflow_execution.workflow_execution_id,
            'status': x.status,
            'properties': x.properties,
            'start_date': parse_date(x.start_date),
            'end_date': parse_date(x.end_date),
            'execution_label': x.execution_label
        },
    )


@init_config
def job_start_execution(args):
    """Starts the job execution by job name and workflow execution id."""
    job_execution = start_job_execution(args.job_name, args.workflow_execution_id)
    print("Job: {}, workflow execution: {}, started: {}.".format(args.job_name, args.workflow_execution_id,
                                                                 job_execution is not None))


@init_config
def job_stop_execution(args):
    """Stops the job execution by job name and workflow execution id."""
    job_execution = stop_job_execution(args.job_name, args.workflow_execution_id)
    print("Job: {}, workflow execution: {}, stopped: {}.".format(args.job_name, args.workflow_execution_id,
                                                                 job_execution is not None))


@init_config
def job_stop_scheduling(args):
    """Stops scheduling the job by job name and workflow execution id."""
    stop_scheduling_job(job_name=args.job_name, execution_id=args.workflow_execution_id)
    print("Job: {}, workflow execution: {}, stop scheduling.".format(args.job_name, args.workflow_execution_id))


@init_config
def job_resume_scheduling(args):
    """Resumes scheduling the job by job name and workflow execution id."""
    resume_scheduling_job(job_name=args.job_name, execution_id=args.workflow_execution_id)
    print("Job: {}, workflow execution: {}, resume scheduling.".format(args.job_name, args.workflow_execution_id))
