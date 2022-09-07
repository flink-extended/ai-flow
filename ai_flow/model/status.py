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
from enum import Enum


class WorkflowStatus(str, Enum):
    """
    Enumeration of WorkflowExecution's status.
    INIT: The initial status of WorkflowExecution.
    RUNNING: The WorkflowExecution is running.
    SUCCESS: The WorkflowExecution finished running without errors.
    FAILED: The WorkflowExecution had errors during execution and failed to run.
    STOPPED: The WorkflowExecution has been stopped.
    """
    INIT = 'INIT'
    RUNNING = 'RUNNING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    STOPPED = 'STOPPED'


class TaskStatus(str, Enum):
    """
    Enumeration of TaskExecution's status.
    INIT: The initial status of TaskExecution.
    QUEUED: The TaskExecution has been assigned to an executor.
    RESTARTING: The TaskExecution was requested to restart when it was running
    RUNNING: The TaskExecution is running.
    SUCCESS: The TaskExecution finished running without errors.
    FAILED: The TaskExecution had errors during execution and failed to run.
    KILLING: The TaskExecution was externally requested to shut down when it was running.
    KILLED: The TaskExecution was externally shut down.
    RETRYING: The TaskExecution failed, but has retry attempts left and will be rescheduled.
    """
    INIT = 'INIT'
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    STOPPING = 'STOPPING'
    STOPPED = 'STOPPED'
    RETRYING = 'RETRYING'


TASK_FINISHED_SET = frozenset(
    [
        TaskStatus.SUCCESS,
        TaskStatus.FAILED,
        TaskStatus.STOPPED,
    ]
)


TASK_ALIVE_SET = frozenset(
    [
        TaskStatus.INIT,
        TaskStatus.QUEUED,
        TaskStatus.RETRYING,
        TaskStatus.RUNNING
    ]
)

WORKFLOW_FINISHED_SET = frozenset(
[
        WorkflowStatus.SUCCESS,
        WorkflowStatus.FAILED,
        WorkflowStatus.STOPPED,
    ]
)

WORKFLOW_ALIVE_SET = frozenset(
[
        WorkflowStatus.INIT,
        WorkflowStatus.RUNNING,
    ]
)
