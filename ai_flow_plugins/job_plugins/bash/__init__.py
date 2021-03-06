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
from ai_flow.plugin_interface import register_job_plugin_factory
from ai_flow_plugins.job_plugins.bash.bash_job_plugin import BashJobPluginFactory
from ai_flow_plugins.job_plugins.bash.bash_processor import BashProcessor
from ai_flow_plugins.job_plugins.bash.bash_job_config import BashJobConfig

register_job_plugin_factory(BashJobPluginFactory())
