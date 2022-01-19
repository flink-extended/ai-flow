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
import ai_flow as af
from wordcount_processor import WordCountProcessor, WordCountSqlProcessor

# Initialize the project and workflow environment.
af.init_ai_flow_context()

# Define a job with process_flink_job config.
with af.job_config('process_flink_job'):
    # Define the flink job.
    af.user_define_operation(processor=WordCountProcessor())

# The run_job event will trigger the process_flink_job job to run.
af.action_on_event(job_name='process_flink_job',
                   event_key='run_job',
                   event_value='process_flink_job',
                   event_type='*',
                   sender='*',
                   namespace='*')

# Define a job with cluster_flink_job config.
with af.job_config('cluster_flink_job'):
    # Define the flink job.
    af.user_define_operation(processor=WordCountProcessor())

# The run_job event will trigger the cluster_flink_job job to run.
af.action_on_event(job_name='cluster_flink_job',
                   event_key='run_job',
                   event_value='cluster_flink_job',
                   event_type='*',
                   sender='*',
                   namespace='*')

# Define a job with sql_flink_job config.
with af.job_config('sql_flink_job'):
    # Define the flink job.
    af.user_define_operation(processor=WordCountSqlProcessor())

# The run_job event will trigger the sql_flink_job job to run.
af.action_on_event(job_name='sql_flink_job',
                   event_key='run_job',
                   event_value='sql_flink_job',
                   event_type='*',
                   sender='*',
                   namespace='*')
