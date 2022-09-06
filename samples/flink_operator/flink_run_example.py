#
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
#
from ai_flow.common.env import expand_env_var
from ai_flow.model.action import TaskAction
from ai_flow.model.status import TaskStatus
from ai_flow.model.workflow import Workflow
from ai_flow.operators.flink.flink_operator import FlinkOperator


with Workflow(name='flink_workflow') as workflow:
    batch_jar = expand_env_var('${FLINK_HOME}/examples/batch/WordCount.jar')
    streaming_jar = expand_env_var('${FLINK_HOME}/examples/streaming/TopSpeedWindowing.jar')

    batch_task = FlinkOperator(name='flink-batch-task',
                               target='yarn-per-job',
                               application=batch_jar)
    streaming_task = FlinkOperator(name='flink-streaming-task',
                                   target='yarn-per-job',
                                   application=streaming_jar)

    streaming_task.start_after([batch_task, ])



