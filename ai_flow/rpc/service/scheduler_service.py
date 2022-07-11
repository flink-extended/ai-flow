## Copyright 2022 The AI Flow Authors
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
import logging
from typing import List

from notification_service.event import Event
from notification_service.notification_client import ListenerProcessor

from ai_flow.model.status import WORKFLOW_ALIVE_SET, WorkflowStatus, WORKFLOW_FINISHED_SET
from ai_flow.rpc.client.aiflow_client import get_notification_client
from ai_flow.rpc.server.exceptions import AIFlowRpcServerException
from ai_flow.rpc.service.util.meta_to_proto import MetaToProto
from ai_flow.common.result import BaseResult, RetCode
from ai_flow.model.internal.events import StartWorkflowExecutionEvent, StopWorkflowExecutionEvent, \
    StartTaskExecutionEvent, StopTaskExecutionEvent
from ai_flow.rpc.service.util.response_wrapper import catch_exception, wrap_result_response, wrap_data_response, \
    wrap_workflow_list_response, wrap_workflow_execution_list_response, wrap_workflow_schedule_list_response, \
    wrap_workflow_trigger_list_response, wrap_task_execution_list_response, wrap_namespace_list_response, \
    wrap_workflow_snapshot_list_response
from ai_flow.metadata.metadata_manager import MetadataManager, Filters, FilterIn
from ai_flow.common.util.db_util.session import create_session
from ai_flow.rpc.protobuf import scheduler_service_pb2_grpc
from ai_flow.scheduler.scheduler import EventDrivenScheduler


class Processor(ListenerProcessor):
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def process(self, events: List[Event]):
        for event in events:
            self.scheduler.trigger(event)


class SchedulerService(scheduler_service_pb2_grpc.SchedulerServiceServicer):

    def __init__(self):
        self.scheduler = EventDrivenScheduler()
        self.notification_client = None
        self.event_listener = None

    def start(self):
        logging.info('Starting scheduler service.')
        self.scheduler.start()
        self.notification_client = get_notification_client(namespace='scheduler', sender='scheduler')
        self.event_listener = self.notification_client.register_listener(
            listener_processor=Processor(self.scheduler), offset=self.get_last_committed_offset())

    def stop(self):
        self.notification_client.unregister_listener(self.event_listener)
        self.scheduler.stop()
        self.notification_client.close()

    def get_last_committed_offset(self):
        # metadata_manager = MetadataManager(self.session)
        return 0

    # begin rpc interface implementation
    @catch_exception
    def addNamespace(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            properties = {}
            if request.properties is not None:
                for key, val in request.properties.items():
                    properties.update({key: val})
            namespace = metadata_manager.add_namespace(request.name, properties)
            return wrap_data_response(MetaToProto.namespace_meta_to_proto(namespace))

    @catch_exception
    def getNamespace(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            namespace = metadata_manager.get_namespace(request.name)
            return wrap_data_response(MetaToProto.namespace_meta_to_proto(namespace))

    @catch_exception
    def updateNamespace(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            namespace = metadata_manager.get_namespace(request.name)
            if namespace is None:
                response = None
            else:
                properties = {}
                if request.properties is not None:
                    for key, val in request.properties.items():
                        properties.update({key: val})
                namespace = metadata_manager.update_namespace(request.name, properties)
                response = MetaToProto.namespace_meta_to_proto(namespace)
            return wrap_data_response(response)

    @catch_exception
    def listNamespaces(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            namespaces = metadata_manager.list_namespace(page_size=request.page_size,
                                                         offset=request.offset)
            return wrap_namespace_list_response(MetaToProto.namespace_meta_list_to_proto(namespaces))

    @catch_exception
    def deleteNamespace(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            namespace = metadata_manager.get_namespace(request.name)
            if namespace is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Namespace {request.name} not exists.'))
            else:
                workflows = metadata_manager.list_workflows(namespace=request.name, page_size=5)
                if len(workflows) > 0:
                    return wrap_result_response(BaseResult(
                        RetCode.ERROR,
                        f'Namespace: {namespace.name} is not empty, please remove all its workflows first.'))
                metadata_manager.delete_namespace(request.name)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def addWorkflow(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            if metadata_manager.get_namespace(request.namespace) is None:
                raise AIFlowRpcServerException(f'Namespace {request.namespace} not exists')
            workflow = metadata_manager.add_workflow(namespace=request.namespace,
                                                     name=request.name,
                                                     content=request.content,
                                                     workflow_object=request.pickled_workflow)
            self.scheduler.dispatcher.rule_extractor.update_workflow(workflow.id, request.pickled_workflow)
        return wrap_data_response(MetaToProto.workflow_meta_to_proto(workflow))

    @catch_exception
    def getWorkflow(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow = metadata_manager.get_workflow_by_name(
                namespace=request.namespace, name=request.workflow_name)
        return wrap_data_response(MetaToProto.workflow_meta_to_proto(workflow))

    @catch_exception
    def updateWorkflow(self, request, context):
        workflow_identifier = request.identifier
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow = metadata_manager.get_workflow_by_name(
                workflow_identifier.namespace, workflow_identifier.workflow_name)
            if workflow is None:
                raise AIFlowRpcServerException(
                    f'Workflow {workflow_identifier.namespace}.{workflow_identifier.workflow_name} not exists')
            else:
                workflow = metadata_manager.update_workflow(namespace=workflow_identifier.namespace,
                                                            name=workflow_identifier.workflow_name,
                                                            content=request.content,
                                                            workflow_object=request.pickled_workflow,
                                                            is_enabled=request.is_enabled)
                if workflow.is_enabled:
                    self.scheduler.dispatcher.rule_extractor.update_workflow(workflow.id, request.pickled_workflow)
                else:
                    self.scheduler.dispatcher.rule_extractor.delete_workflow(workflow.id)
                response = MetaToProto.workflow_meta_to_proto(workflow)
        return wrap_data_response(response)

    @catch_exception
    def deleteWorkflow(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow = metadata_manager.get_workflow_by_name(request.namespace, request.workflow_name)
            if workflow is None:
                return wrap_result_response(BaseResult(
                    RetCode.ERROR, f'Workflow {request.namespace}.{request.workflow_name} not exists'))
            else:
                metadata_manager.delete_workflow_by_name(request.namespace, request.workflow_name)
                self.scheduler.dispatcher.rule_extractor.delete_workflow(workflow.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def listWorkflows(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflows = metadata_manager.list_workflows(namespace=request.namespace,
                                                        page_size=request.page_size,
                                                        offset=request.offset)
        return wrap_workflow_list_response(MetaToProto.workflow_meta_list_to_proto(workflows))

    @catch_exception
    def disableWorkflow(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow = metadata_manager.get_workflow_by_name(request.namespace, request.workflow_name)
            if workflow is None:
                return wrap_result_response(BaseResult(
                    RetCode.ERROR, f'Workflow {request.namespace}.{request.workflow_name} not exists'))
            else:
                metadata_manager.update_workflow(request.namespace, request.workflow_name, is_enabled=False)
                self.scheduler.dispatcher.rule_extractor.delete_workflow(workflow.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def enableWorkflow(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow = metadata_manager.get_workflow_by_name(request.namespace, request.workflow_name)
            if workflow is None:
                return wrap_result_response(BaseResult(
                    RetCode.ERROR, f'Workflow {request.namespace}.{request.workflow_name} not exists'))
            else:
                metadata_manager.update_workflow(request.namespace, request.workflow_name, is_enabled=True)
            self.scheduler.dispatcher.rule_extractor.update_workflow(workflow.id, workflow.workflow_object)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def addWorkflowSnapshot(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            uri = request.uri.value if request.HasField('uri') else None
            signature = request.signature.value if request.HasField('signature') else None
            workflow_snapshot = metadata_manager.add_workflow_snapshot(
                request.workflow_id, uri, request.workflow_object, signature)
            return wrap_data_response(MetaToProto.workflow_snapshot_meta_to_proto(workflow_snapshot))

    @catch_exception
    def getWorkflowSnapshot(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_snapshot = metadata_manager.get_workflow_snapshot(request.id)
            return wrap_data_response(MetaToProto.workflow_snapshot_meta_to_proto(workflow_snapshot))

    @catch_exception
    def listWorkflowSnapshots(self, request, context):
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            if workflow_meta is None:
                raise AIFlowRpcServerException(f'Workflow {namespace}.{workflow_name} not exists')
            workflow_snapshots = metadata_manager.list_workflow_snapshots(workflow_id=workflow_meta.id,
                                                                          page_size=request.page_size,
                                                                          offset=request.offset)
            return wrap_workflow_snapshot_list_response(
                MetaToProto.workflow_snapshot_meta_list_to_proto(workflow_snapshots))

    @catch_exception
    def deleteWorkflowSnapshot(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            snapshot = metadata_manager.get_workflow_snapshot(request.id)
            if snapshot is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow snapshot {request.id} not exists'))
            else:
                metadata_manager.delete_workflow_snapshot(request.id)
                # Also need to delete snapshot files after blob manager refactoring
                return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def deleteWorkflowSnapshots(self, request, context):
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            if workflow_meta is None:
                return wrap_result_response(
                    BaseResult(RetCode.ERROR, f'Workflow {namespace}.{workflow_name} not exists'))
            snapshots = metadata_manager.list_workflow_snapshots(workflow_id=workflow_meta.id)
            for snapshot in snapshots:
                metadata_manager.delete_workflow_snapshot(snapshot.id)
                # Also need to delete snapshot files after blob manager refactoring
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def startWorkflowExecution(self, request, context):
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            latest_snapshot = metadata_manager.get_latest_snapshot(workflow_meta.id)
            event = StartWorkflowExecutionEvent(workflow_meta.id, latest_snapshot.id)
            self.notification_client.send_event(event)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def stopWorkflowExecution(self, request, context):
        event = StopWorkflowExecutionEvent(request.id)
        self.notification_client.send_event(event)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def stopWorkflowExecutions(self, request, context):
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            if workflow_meta is None:
                raise AIFlowRpcServerException(f'Workflow {namespace}.{workflow_name} not exists')
            workflow_executions = metadata_manager.list_workflow_executions(
                workflow_id=workflow_meta.id, filters=Filters([(FilterIn('status'), list(WORKFLOW_ALIVE_SET))]))
            for we in workflow_executions:
                event = StopWorkflowExecutionEvent(we.id)
                self.notification_client.send_event(event)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def deleteWorkflowExecution(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            execution = metadata_manager.get_workflow_execution(request.id)
            if execution is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow execution {request.id} not exists'))
            elif WorkflowStatus(execution.status) not in WORKFLOW_FINISHED_SET:
                return wrap_result_response(BaseResult(
                    RetCode.ERROR, f'Workflow execution {request.id} is not finished, cannot be removed.'))
            else:
                while True:
                    task_executions = metadata_manager.list_task_executions(execution.id, page_size=10)
                    if len(task_executions) > 0:
                        for te in task_executions:
                            metadata_manager.delete_task_execution(te.id)
                    else:
                        break
                metadata_manager.delete_workflow_execution(execution.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def getWorkflowExecution(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_execution = metadata_manager.get_workflow_execution(request.id)
        return wrap_data_response(MetaToProto.workflow_execution_meta_to_proto(workflow_execution))

    @catch_exception
    def listWorkflowExecutions(self, request, context):
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            if workflow_meta is None:
                raise AIFlowRpcServerException(f'Workflow {namespace}.{workflow_name} not exists')
            workflow_executions = metadata_manager.list_workflow_executions(workflow_id=workflow_meta.id,
                                                                            page_size=request.page_size,
                                                                            offset=request.offset)
        return wrap_workflow_execution_list_response(
            MetaToProto.workflow_execution_meta_list_to_proto(workflow_executions))

    @catch_exception
    def startTaskExecution(self, request, context):
        event = StartTaskExecutionEvent(request.workflow_execution_id, request.task_name)
        self.notification_client.send_event(event)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def stopTaskExecution(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            task_execution = metadata_manager.get_latest_task_execution(
                workflow_execution_id=request.workflow_execution_id, task_name=request.task_name)
            if task_execution is None:
                raise AIFlowRpcServerException(
                    f'Task execution {request.workflow_execution_id}.{request.task_name} not exists')
            event = StopTaskExecutionEvent(workflow_execution_id=task_execution.workflow_execution_id,
                                           task_execution_id=task_execution.id)
            self.notification_client.send_event(event)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def getTaskExecution(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            task_execution = metadata_manager.get_task_execution_by_id(request.id)
            return wrap_data_response(MetaToProto.task_execution_meta_to_proto(task_execution))

    @catch_exception
    def listTaskExecutions(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_execution = metadata_manager.get_workflow_execution(request.workflow_execution_id)
            if workflow_execution is None:
                raise AIFlowRpcServerException(f'Workflow execution with id: {request.workflow_execution_id} not exists')
            task_executions = metadata_manager.list_task_executions(workflow_execution_id=request.workflow_execution_id,
                                                                    page_size=request.page_size,
                                                                    offset=request.offset)
        return wrap_task_execution_list_response(MetaToProto.task_execution_meta_list_to_proto(task_executions))

    @catch_exception
    def addWorkflowSchedule(self, request, context):
        expression = request.expression.value if request.HasField('expression') else None
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            schedule = metadata_manager.add_workflow_schedule(workflow_id=request.workflow_id,
                                                              expression=expression)
        return wrap_data_response(MetaToProto.workflow_schedule_meta_to_proto(schedule))

    @catch_exception
    def getWorkflowSchedule(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            schedule = metadata_manager.get_workflow_schedule(request.id)
        return wrap_data_response(MetaToProto.workflow_schedule_meta_to_proto(schedule))

    @catch_exception
    def listWorkflowSchedules(self, request, context):
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            if workflow_meta is None:
                raise AIFlowRpcServerException(f'Workflow {namespace}.{workflow_name} not exists')
            schedules = metadata_manager.list_workflow_schedules(workflow_id=workflow_meta.id,
                                                                 page_size=request.page_size,
                                                                 offset=request.offset)
        return wrap_workflow_schedule_list_response(
            MetaToProto.workflow_schedule_meta_list_to_proto(schedules))

    @catch_exception
    def deleteWorkflowSchedule(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            schedule = metadata_manager.get_workflow_schedule(request.id)
            if schedule is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow schedule {request.id} not exists'))
            else:
                metadata_manager.delete_workflow_schedule(schedule.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def deleteWorkflowSchedules(self, request, context):
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            if workflow_meta is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow {namespace}.{workflow_name} not exists'))
            schedules = metadata_manager.list_workflow_schedules(workflow_id=workflow_meta.id)
            for schedule in schedules:
                metadata_manager.delete_workflow_schedule(schedule.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def pauseWorkflowSchedule(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            schedule = metadata_manager.get_workflow_schedule(request.id)
            if schedule is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow schedule {request.id} not exists'))
            else:
                metadata_manager.pause_workflow_schedule(schedule.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def resumeWorkflowSchedule(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            schedule = metadata_manager.get_workflow_schedule(request.id)
            if schedule is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow schedule {request.id} not exists'))
            else:
                metadata_manager.resume_workflow_schedule(schedule.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def addWorkflowTrigger(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            trigger = metadata_manager.add_workflow_trigger(workflow_id=request.workflow_id,
                                                            rule=request.rule)
            self.scheduler.dispatcher.rule_extractor.update_workflow_trigger(trigger)
        return wrap_data_response(MetaToProto.workflow_trigger_meta_to_proto(trigger))

    @catch_exception
    def getWorkflowTrigger(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            trigger = metadata_manager.get_workflow_trigger(request.id)
        return wrap_data_response(MetaToProto.workflow_trigger_meta_to_proto(trigger))

    @catch_exception
    def listWorkflowTriggers(self, request, context):
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            if workflow_meta is None:
                raise AIFlowRpcServerException(f'Workflow {namespace}.{workflow_name} not exists')
            triggers = metadata_manager.list_workflow_triggers(workflow_id=workflow_meta.id,
                                                               page_size=request.page_size,
                                                               offset=request.offset)
        return wrap_workflow_trigger_list_response(
            MetaToProto.workflow_trigger_meta_list_to_proto(triggers))

    @catch_exception
    def deleteWorkflowTrigger(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            trigger = metadata_manager.get_workflow_trigger(request.id)
            if trigger is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow trigger {request.id} not exists'))
            else:
                metadata_manager.delete_workflow_trigger(trigger.id)
                self.scheduler.dispatcher.rule_extractor.delete_workflow_trigger(trigger.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def deleteWorkflowTriggers(self, request, context):
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            if workflow_meta is None:
                raise AIFlowRpcServerException(f'Workflow {namespace}.{workflow_name} not exists')
            triggers = metadata_manager.list_workflow_triggers(workflow_id=workflow_meta.id)
            for trigger in triggers:
                metadata_manager.delete_workflow_trigger(trigger.id)
                self.scheduler.dispatcher.rule_extractor.delete_workflow_trigger(trigger.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def pauseWorkflowTrigger(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            trigger = metadata_manager.get_workflow_trigger(request.id)
            if trigger is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow trigger {request.id} not exists'))
            else:
                metadata_manager.pause_workflow_trigger(trigger.id)
                self.scheduler.dispatcher.rule_extractor.delete_workflow_trigger(trigger.id)
        return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def resumeWorkflowTrigger(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            trigger = metadata_manager.get_workflow_trigger(request.id)
            if trigger is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow trigger {request.id} not exists'))
            else:
                metadata_manager.resume_workflow_trigger(trigger.id)
                self.scheduler.dispatcher.rule_extractor.update_workflow_trigger(trigger)
        return wrap_result_response(BaseResult(RetCode.OK, None))















