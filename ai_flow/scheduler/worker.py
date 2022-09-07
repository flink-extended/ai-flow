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
import json
import logging
import queue
import threading

from notification_service.model.event import Event
from ai_flow.common.util.db_util.session import create_session
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.model.action import TaskAction
from ai_flow.model.internal.events import SchedulingEventType, EventContextConstant, HAS_WORKFLOW_EXECUTION_ID_SET
from ai_flow.model.status import TaskStatus, TASK_ALIVE_SET
from ai_flow.scheduler.rule_executor import RuleExecutor
from ai_flow.scheduler.rule_wrapper import WorkflowRuleWrapper
from ai_flow.scheduler.schedule_command import WorkflowExecutionStartCommand, WorkflowExecutionStopCommand, \
    WorkflowExecutionScheduleCommand
from ai_flow.scheduler.scheduling_event_processor import SchedulingEventProcessor
from ai_flow.scheduler.scheduling_unit import SchedulingUnit
from ai_flow.scheduler.workflow_executor import WorkflowExecutor
from ai_flow.task_executor.task_executor import TaskExecutor


class Worker(threading.Thread):
    """Worker's responsibility is executing the scheduling unit."""

    def __init__(self,
                 max_queue_size: int = 20,
                 task_executor: TaskExecutor = None):
        super().__init__()
        self.input_queue = queue.Queue(max_queue_size)
        self.task_executor = task_executor
        self._last_committed_offset = None

    def add_unit(self, unit: SchedulingUnit):
        self.input_queue.put(unit)

    @property
    def last_committed_offset(self):
        return self._last_committed_offset

    def _execute_workflow_execution_schedule_command(self,
                                                     command: WorkflowExecutionScheduleCommand,
                                                     metadata_manager: MetadataManager):
        for c in command.task_schedule_commands:
            self.task_executor.schedule_task(c)
            # set the task execution status
            if TaskAction.START == c.action or TaskAction.RESTART == c.action:
                task_execution_meta = metadata_manager.get_task_execution(
                    workflow_execution_id=c.new_task_execution.workflow_execution_id,
                    task_name=c.new_task_execution.task_name,
                    sequence_number=c.new_task_execution.seq_num)
                if TaskStatus.INIT == TaskStatus(task_execution_meta.status):
                    metadata_manager.update_task_execution(task_execution_id=task_execution_meta.id,
                                                           status=TaskStatus.QUEUED.value)
            if TaskAction.STOP == c.action or (TaskAction.RESTART == c.action and c.current_task_execution is not None):
                task_execution_meta = metadata_manager.get_task_execution(
                    workflow_execution_id=c.current_task_execution.workflow_execution_id,
                    task_name=c.current_task_execution.task_name,
                    sequence_number=c.current_task_execution.seq_num)
                if TaskStatus(task_execution_meta.status) in TASK_ALIVE_SET:
                    metadata_manager.update_task_execution(task_execution_id=task_execution_meta.id,
                                                           status=TaskStatus.STOPPING.value)

    @staticmethod
    def _process_scheduling_event(scheduling_event_processor, workflow_executor, event):
        command = scheduling_event_processor.process(event=event)
        if isinstance(command, WorkflowExecutionStartCommand) \
                or isinstance(command, WorkflowExecutionStopCommand):
            schedule_command = workflow_executor.execute(command)
            return schedule_command
        elif isinstance(command, WorkflowExecutionScheduleCommand):
            return command

    @staticmethod
    def _set_event_offset_by_scheduling_event(metadata_manager: MetadataManager, event: Event):
        scheduling_event_type = SchedulingEventType(event.value)
        context = json.loads(event.context)
        if SchedulingEventType.START_WORKFLOW_EXECUTION == scheduling_event_type:
            workflow_id = context[EventContextConstant.WORKFLOW_ID]
            metadata_manager.set_workflow_event_offset(workflow_id=workflow_id, event_offset=event.offset)
        elif SchedulingEventType.PERIODIC_RUN_WORKFLOW == scheduling_event_type:
            workflow_id = context[EventContextConstant.WORKFLOW_ID]
            metadata_manager.set_workflow_event_offset(workflow_id=workflow_id,
                                                       event_offset=event.offset)
        elif scheduling_event_type in HAS_WORKFLOW_EXECUTION_ID_SET:
            workflow_execution_id = context[EventContextConstant.WORKFLOW_EXECUTION_ID]
            metadata_manager.set_workflow_execution_event_offset(workflow_execution_id=workflow_execution_id,
                                                                 event_offset=event.offset)
        else:
            logging.warning("Ignore setting the event offset: {}.".format(str(event)))

    def run(self) -> None:
        with create_session() as session:
            metadata_manager = MetadataManager(session=session)
            scheduling_event_processor = SchedulingEventProcessor(metadata_manager=metadata_manager)
            workflow_executor = WorkflowExecutor(metadata_manager=metadata_manager)
            rule_executor = RuleExecutor(metadata_manager=metadata_manager)
            while True:
                try:
                    event, rule = self.input_queue.get()
                    if event is None:
                        logging.info('scheduler worker {} is stopped!'.format(self.name))
                        break
                    schedule_command = None
                    if rule is None:
                        schedule_command = self._process_scheduling_event(scheduling_event_processor,
                                                                          workflow_executor,
                                                                          event)
                        self._set_event_offset_by_scheduling_event(metadata_manager, event)
                    else:
                        if isinstance(rule, WorkflowRuleWrapper):
                            command = rule_executor.execute_workflow_rule(event=event, rule=rule)
                            if command is not None:
                                schedule_command = workflow_executor.execute(command)
                            metadata_manager.set_workflow_event_offset(workflow_id=rule.workflow_id,
                                                                       event_offset=event.offset)
                        else:
                            schedule_command = rule_executor.execute_workflow_execution_rule(event=event, rule=rule)
                            metadata_manager.set_workflow_execution_event_offset(
                                workflow_execution_id=rule.workflow_execution_id,
                                event_offset=event.offset)
                    if schedule_command is not None:
                        self._execute_workflow_execution_schedule_command(command=schedule_command,
                                                                          metadata_manager=metadata_manager)
                    metadata_manager.commit()
                    self._last_committed_offset = event.offset
                except Exception as e:
                    session.rollback()
                    logging.exception(
                        "Can not handle event: {}, exception: {}".format(str(event), str(e)))
                finally:
                    self.input_queue.task_done()

    def stop(self):
        self.input_queue.put((None, None))
        self.join()
