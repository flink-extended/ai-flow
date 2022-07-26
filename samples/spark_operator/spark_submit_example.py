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
from ai_flow.operators.spark.spark_submit import SparkSubmitOperator
from ai_flow.model.workflow import Workflow


with Workflow(name='spark_workflow') as workflow:
    application_path = expand_env_var('${SPARK_HOME}/examples/jars/spark-examples_2.12-3.2.1.jar')
    task = SparkSubmitOperator(name='spark-submit-example-task',
                               application=application_path,
                               application_args=['100'],
                               master='local[2]',
                               application_name='spark_operator_example',
                               submit_options='--class org.apache.spark.examples.SparkPi')
