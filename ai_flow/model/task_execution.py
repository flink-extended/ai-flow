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
import logging
import signal
from datetime import datetime

from typing import List

from ai_flow.common.exception.exceptions import TaskForceStoppedException, TaskFailedException
from ai_flow.common.util import workflow_utils
from ai_flow.model import workflow_execution
from ai_flow.model.context import Context
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.operator import AIFlowOperator
from ai_flow.model.status import TaskStatus
from ai_flow.model.workflow import Workflow

logger = logging.getLogger(__name__)


class TaskExecutionKey(object):
    def __init__(self,
                 workflow_execution_id,
                 task_name,
                 seq_num):
        self.workflow_execution_id = workflow_execution_id
        self.task_name = task_name
        self.seq_num = seq_num

    def __str__(self):
        return '{}_{}_{}'.format(self.workflow_execution_id, self.task_name, self.seq_num)


class TaskExecution(object):
    """
    TaskExecution describes an instance of a task. It can be created by the scheduler.
    """
    def __init__(self,
                 workflow_execution_id: int,
                 task_name: str,
                 sequence_number: int,
                 execution_type: ExecutionType,
                 begin_date: datetime = None,
                 end_date: datetime = None,
                 status: TaskStatus = TaskStatus.INIT,
                 id: int = None
                 ):
        """
        :param workflow_execution_id: TaskExecution belongs to the unique identifier of WorkflowExecution.
        :param task_name: The name of the task it belongs to.
        :param sequence_number: A task in a WorkflowExecution can be run multiple times,
                                it indicates how many times this task is run.
        :param execution_type: The type that triggers TaskExecution.
        :param begin_date: The time TaskExecution started executing.
        :param end_date: The time TaskExecution ends execution.
        :param status: TaskExecution's current status.
        :param id: Unique ID of TaskExecution.
        """
        self.id = id
        self.workflow_execution_id = workflow_execution_id
        self.task_name = task_name
        self.sequence_number = sequence_number
        self.execution_type = execution_type
        self.begin_date = begin_date
        self.end_date = end_date
        self.status = status

        self.try_number = 0

    def get_task(self):
        snapshot_path = workflow_execution.get_workflow_snapshot(self.workflow_execution_id)
        workflows: List[Workflow] = workflow_utils.extract_workflow(snapshot_path)
        name = workflow_execution.get_workflow_name_by_execution_id(self.workflow_execution_id)
        workflows = [x for x in workflows if x.name == name]
        assert len(workflows) == 1
        return workflows[0].tasks.get(self.task_name)

    def run(self):
        task = self.get_task()
        try:
            if isinstance(task, AIFlowOperator):

                def signal_handler(signum, frame):  # pylint: disable=unused-argument
                    logger.error("Received SIGTERM. Terminating subprocesses.")
                    task.stop()
                    raise TaskForceStoppedException("Task received SIGTERM signal")
                signal.signal(signal.SIGTERM, signal_handler)

                context = Context()
                task.start(context)
                task.await_termination(context)
        except TaskForceStoppedException:
            self.handle_force_kill()
            raise
        except (Exception, KeyboardInterrupt) as e:
            self._run_failure_callback()
            raise TaskFailedException(e)
        finally:
            logger.info(f'ti.finish.{task.dag_id}.{task.task_id}.{self.state}')

        self._run_success_callback(context, task)

    def is_eligible_to_retry(self, task):
        """Is task execution is eligible for retry"""
        max_tries = task.config.get('max_tries')
        return max_tries is not None and self.try_number <= max_tries

    def handle_force_kill(self):
        pass

    def _run_success_callback(self, context, task):
        pass

    def _run_failure_callback(self, context, task):
        pass
