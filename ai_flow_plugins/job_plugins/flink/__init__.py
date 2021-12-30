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
from pyflink.version import __version__

from ai_flow.endpoint.server.exception import AIFlowException
from ai_flow.plugin_interface import register_job_plugin_factory
from ai_flow_plugins.job_plugins.flink.flink_env import set_flink_env, FlinkEnv, \
    FlinkBatchEnv, FlinkStreamEnv
from ai_flow_plugins.job_plugins.flink.flink_job_config import FlinkJobConfig
from ai_flow_plugins.job_plugins.flink.flink_job_plugin import FlinkJobPluginFactory
from ai_flow_plugins.job_plugins.flink.flink_processor import FlinkPythonProcessor, FlinkJavaProcessor, \
    ExecutionContext, FlinkSqlProcessor, UDFWrapper
from ai_flow_plugins.job_plugins.flink.flink_version import INCLUDE_DATASET_VERSIONS

if __version__ in INCLUDE_DATASET_VERSIONS:
    from ai_flow_plugins.job_plugins.flink.flink_env import WrappedBatchTableEnvironment, WrappedStreamTableEnvironment
elif '1.13' in __version__ or '1.14' in __version__:
    from ai_flow_plugins.job_plugins.flink.flink_env import WrappedTableEnvironment
else:
    raise AIFlowException("Flink job plugin only supports the Flink versions: 1.11, 1.12, 1.13 and 1.14.")

register_job_plugin_factory(FlinkJobPluginFactory())
