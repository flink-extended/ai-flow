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

from ai_flow.rpc.service.util.meta_to_proto import MetaToProto
from notification_service.embedded_notification_client import EmbeddedNotificationClient

from ai_flow.common.configuration import config_constants
from ai_flow.common.result import BaseResult, RetCode
from ai_flow.model.internal.events import StartWorkflowExecutionEvent
from ai_flow.rpc.service.util.response_wrapper import catch_exception, wrap_result_response, wrap_data_response, \
    wrap_workflow_list_response
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.common.util.db_util.session import create_session, create_sqlalchemy_engine
from ai_flow.rpc.protobuf import scheduler_service_pb2_grpc
from ai_flow.scheduler.scheduler import EventDrivenScheduler


class SchedulerService(scheduler_service_pb2_grpc.SchedulerServiceServicer):

    def __init__(self):
        db_engine = create_sqlalchemy_engine(config_constants.METADATA_BACKEND_URI)
        self.notification_client = EmbeddedNotificationClient(
            server_uri=config_constants.NOTIFICATION_SERVER_URI,
            namespace='scheduler', sender='scheduler')
        self.scheduler = EventDrivenScheduler(db_engine=db_engine,
                                              notification_client=self.notification_client)

    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.stop()

    @catch_exception
    def addWorkflow(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
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
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_identifier = request.identifier
            workflow = metadata_manager.get_workflow_by_name(
                workflow_identifier.namespace, workflow_identifier.workflow_name)
            if workflow is None:
                response = None
            else:
                workflow = metadata_manager.update_workflow(namespace=workflow_identifier.namespace,
                                                            name=workflow_identifier.workflow_name,
                                                            content=request.content,
                                                            workflow_object=request.pickled_workflow,
                                                            is_enabled=request.is_enabled)
                self.scheduler.dispatcher.rule_extractor.update_workflow(workflow.id, request.pickled_workflow)
                response = MetaToProto.workflow_meta_to_proto(workflow)
            return wrap_data_response(response)

    @catch_exception
    def deleteWorkflow(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow = metadata_manager.get_workflow_by_name(request.namespace, request.workflow_name)
            if workflow is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow {request.workflow_name} not exists'))
            else:
                metadata_manager.delete_workflow_by_name(request.namespace, request.workflow_name)
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
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow {request.workflow_name} not exists'))
            else:
                metadata_manager.update_workflow(request.namespace, request.workflow_name, is_enabled=False)
                return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def enableWorkflow(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow = metadata_manager.get_workflow_by_name(request.namespace, request.workflow_name)
            if workflow is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow {request.workflow_name} not exists'))
            else:
                metadata_manager.update_workflow(request.namespace, request.workflow_name, is_enabled=True)
                return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def startWorkflowExecution(self, request, context):
        # Return nothing because currently we reuse the scheduler logic, so this call is async now.
        # Maybe make it sync and return workflow execution id.
        namespace = request.namespace
        workflow_name = request.workflow_name
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_meta = metadata_manager.get_workflow_by_name(namespace, workflow_name)
            latest_snapshot = metadata_manager.get_latest_snapshot(workflow_meta.id)
        event = StartWorkflowExecutionEvent(workflow_meta.id, latest_snapshot.id)
        self.notification_client.send_event(event)
        return wrap_result_response(BaseResult(RetCode.OK, None))






