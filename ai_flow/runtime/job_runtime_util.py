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
import os
import time

from ai_flow.plugin_interface.scheduler_interface import JobExecutionInfo
from ai_flow.context.project_context import ProjectContext
from ai_flow.runtime.job_runtime_env import JobRuntimeEnv


def prepare_job_runtime_env(workflow_generated_dir,
                            workflow_name,
                            project_context: ProjectContext,
                            job_execution_info: JobExecutionInfo,
                            root_working_dir=None,
                            base_log_folder=None) -> JobRuntimeEnv:
    """
    Prepare the operating environment for the ai flow job(ai_flow.workflow.job.Job)
    :param workflow_generated_dir: The generated directory of workflow.
    :param workflow_name: The name of the workflow(ai_flow.workflow.workflow.Workflow).
    :param project_context: The context of the project which the job belongs.
    :param job_execution_info: The information of the execution of the job.
    :param root_working_dir: The working directory of the execution of the job(ai_flow.workflow.job.Job).
    :param base_log_folder: The base folder of the logs.
    :return: ai_flow.runtime.job_runtime_env.JobRuntimeEnv object.
    """
    working_dir = os.path.join(root_working_dir,
                               workflow_name,
                               job_execution_info.job_name,
                               str(time.strftime("%Y%m%d%H%M%S", time.localtime())))
    job_runtime_env: JobRuntimeEnv = JobRuntimeEnv(working_dir=working_dir,
                                                   job_execution_info=job_execution_info,
                                                   project_context=project_context,
                                                   base_log_folder=base_log_folder)
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
        job_runtime_env.save_job_execution_info()
        if not os.path.exists(job_runtime_env.log_dir):
            os.makedirs(job_runtime_env.log_dir)
        if not os.path.exists(os.path.dirname(job_runtime_env.workflow_dir)):
            os.makedirs(os.path.dirname(job_runtime_env.workflow_dir))
        if not os.path.exists(job_runtime_env.workflow_dir):
            os.symlink(project_context.get_workflow_path(workflow_name=workflow_name),
                       job_runtime_env.workflow_dir)
        if os.path.exists(project_context.get_generated_path()):
            os.symlink(os.path.join(project_context.get_generated_path(),
                                    workflow_generated_dir,
                                    job_execution_info.job_name),
                       job_runtime_env.generated_dir)
        if os.path.exists(project_context.get_resources_path()):
            os.symlink(project_context.get_resources_path(), job_runtime_env.resource_dir)
        if os.path.exists(project_context.get_dependencies_path()):
            os.symlink(project_context.get_dependencies_path(), job_runtime_env.dependencies_dir)
        os.symlink(project_context.get_project_config_file(), job_runtime_env.project_config_file)
    return job_runtime_env
