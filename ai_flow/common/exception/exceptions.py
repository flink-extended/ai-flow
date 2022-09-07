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


class AIFlowException(Exception):
    """Base exception of AIFlow"""


class AIFlowConfigException(AIFlowException):
    """Raise when there is configuration problem"""


class AIFlowDBException(AIFlowException):
    """Raise when there is database problem"""


class AIFlowYAMLException(AIFlowException):
    """Raise when there is yaml handling problem"""


class TaskFailedException(AIFlowException):
    """Raise when the task execution failed"""


class TaskForceStoppedException(AIFlowException):
    """Raise when task execution is force killed"""


class AIFlowK8sException(AIFlowException):
    """Raise when there is a k8s related error"""
