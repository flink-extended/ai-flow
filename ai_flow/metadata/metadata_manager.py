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
from typing import List, Optional, Tuple, Any

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.time_utils import utcnow
from ai_flow.metadata.namespace import NamespaceMeta
from ai_flow.metadata.state import DBWorkflowValueState, DBWorkflowExecutionValueState
from ai_flow.metadata.task_execution import TaskExecutionMeta
from ai_flow.metadata.workflow import WorkflowMeta
from ai_flow.metadata.workflow_event_trigger import WorkflowEventTriggerMeta
from ai_flow.metadata.workflow_execution import WorkflowExecutionMeta
from ai_flow.metadata.workflow_schedule import WorkflowScheduleMeta
from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta
from sqlalchemy import asc, desc

from ai_flow.model.state import StateDescriptor, State, ValueStateDescriptor
from ai_flow.model.status import TaskStatus


class BaseFilter(object):
    column_name = None

    def __init__(self, column_name):
        self.column_name = column_name

    def apply(self, criterion, query, value):
        raise NotImplementedError


class Filters(object):
    filters: List[Tuple[BaseFilter, Any]] = None

    def __init__(self, filters: List[Tuple[BaseFilter, Any]] = None):
        self.filters = filters if filters else []

    def add_filter(self, f: Tuple[BaseFilter, Any]):
        self.filters.append(f)

    def apply_all(self, criterion, query):
        for flt, value in self.filters:
            query = flt.apply(criterion, query, value)
        return query

    def __repr__(self):
        ret_str = 'Filters:'
        for flt, value in self.filters:
            ret_str = ret_str + '%s:%s\n' % (
                str(flt.column_name),
                str(value),
            )
        return ret_str


class BaseOrder(object):
    column_name = None

    def __init__(self, column_name):
        self.column_name = column_name

    def apply(self, criterion, query, direction):
        raise NotImplementedError


class Orders(object):
    orders: List[Tuple[BaseOrder, str]] = None

    def __init__(self, orders: List[Tuple[BaseOrder, str]] = None):
        self.orders = orders if orders else []

    def add_order(self, o: Tuple[BaseOrder, str]):
        self.orders.append(o)

    def apply_all(self, criterion, query):
        for order, direction in self.orders:
            query = order.apply(criterion, query, direction)
        return query

    def __repr__(self):
        ret_str = 'Orders:'
        for order, direction in self.orders:
            ret_str = ret_str + '%s:%s\n' % (
                str(order.column_name),
                str(direction),
            )
        return ret_str


class FilterEqual(BaseFilter):

    def apply(self, criterion, query, value):
        return query.filter(getattr(criterion, self.column_name) == value)


class OrderBy(BaseOrder):

    def apply(self, criterion, query, value):
        if value == 'ascend':
            return query.order_by(asc(getattr(criterion, self.column_name)))
        elif value == 'descend':
            return query.order_by(desc(getattr(criterion, self.column_name)))


class MetadataManager(object):
    def __init__(self, session):
        self.session = session

    # begin namespace
    def add_namespace(self, name, properties) -> NamespaceMeta:
        try:
            namespace_meta = NamespaceMeta(name=name, properties=properties)
            self.session.add(namespace_meta)
            self.session.commit()
            return namespace_meta
        except Exception as e:
            self.session.rollback()
            raise e

    def update_namespace(self, name, properties) -> NamespaceMeta:
        try:
            namespace_meta = self.session.query(NamespaceMeta).filter(NamespaceMeta.name == name).one()
            namespace_meta.set_properties(properties)
            self.session.merge(namespace_meta)
            self.session.commit()
            return namespace_meta
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_namespace(self, name):
        try:
            self.session.query(NamespaceMeta).filter(NamespaceMeta.name == name).delete()
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_namespace(self, name) -> NamespaceMeta:
        return self.session.query(NamespaceMeta).filter(NamespaceMeta.name == name).one()

    def list_namespace(self) -> List[NamespaceMeta]:
        return self.session.query(NamespaceMeta).all()

    # end namespace

    # begin workflow
    def add_workflow(self, namespace, name, content, workflow_object) -> WorkflowMeta:
        try:
            workflow_meta = WorkflowMeta(namespace=namespace,
                                         name=name,
                                         content=content,
                                         workflow_object=workflow_object)
            self.session.add(workflow_meta)
            self.session.commit()
            return workflow_meta
        except Exception as e:
            self.session.rollback()
            raise e

    def get_workflow_by_name(self, namespace, name) -> WorkflowMeta:
        return self.session.query(WorkflowMeta).filter(WorkflowMeta.namespace == namespace,
                                                       WorkflowMeta.name == name).first()

    def get_workflow_by_id(self, workflow_id) -> Optional[WorkflowMeta]:
        return self.session.query(WorkflowMeta).filter(WorkflowMeta.id == workflow_id).first()

    def list_workflows(self,
                       namespace,
                       page_size=10,
                       offset=None,
                       filters: Filters = None,
                       orders: Orders = None) -> List[WorkflowMeta]:
        query = self.session.query(WorkflowMeta).filter(WorkflowMeta.namespace == namespace)
        if filters:
            query = filters.apply_all(WorkflowMeta, query)
        if orders:
            query = orders.apply_all(WorkflowMeta, query)
        if page_size:
            query = query.limit(page_size)
        if offset:
            query = query.offset(offset)
        return query.all()

    def delete_workflow_by_name(self, namespace, workflow_name):
        try:
            self.session.query(WorkflowMeta).filter(WorkflowMeta.namespace == namespace,
                                                    WorkflowMeta.name == workflow_name).delete()
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_workflow_by_id(self, workflow_id):
        try:
            self.session.query(WorkflowMeta).filter(WorkflowMeta.id == workflow_id).delete()
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def update_workflow(self, namespace, name, content=None, workflow_object=None, enable=None) -> WorkflowMeta:
        try:
            workflow_meta = self.session.query(WorkflowMeta).filter(WorkflowMeta.namespace == namespace,
                                                                    WorkflowMeta.name == name).one()
            if content is not None:
                workflow_meta.context = content
            if workflow_object is not None:
                workflow_meta.workflow_object = workflow_object
            if enable is not None:
                workflow_meta.enable = enable
            workflow_meta.update_time = utcnow()
            self.session.merge(workflow_meta)
            self.session.commit()
            return workflow_meta
        except Exception as e:
            self.session.rollback()
            raise e

    # end workflow

    # begin workflow snapshot
    def add_workflow_snapshot(self, workflow_id, uri, workflow_object, signature) -> WorkflowSnapshotMeta:
        try:
            workflow_snapshot_meta = WorkflowSnapshotMeta(workflow_id=workflow_id,
                                                          uri=uri,
                                                          workflow_object=workflow_object,
                                                          signature=signature)
            self.session.add(workflow_snapshot_meta)
            self.session.commit()
            return workflow_snapshot_meta
        except Exception as e:
            self.session.rollback()
            raise e

    def get_workflow_snapshot(self, snapshot_id) -> WorkflowSnapshotMeta:
        return self.session.query(WorkflowSnapshotMeta).filter(WorkflowSnapshotMeta.id == snapshot_id).first()

    def list_workflow_snapshots(self,
                                workflow_id,
                                page_size=10,
                                offset=None,
                                filters: Filters = None,
                                orders: Orders = None) -> List[WorkflowSnapshotMeta]:
        query = self.session.query(WorkflowSnapshotMeta).filter(WorkflowSnapshotMeta.workflow_id == workflow_id)
        if filters:
            query = filters.apply_all(WorkflowSnapshotMeta, query)
        if orders:
            query = orders.apply_all(WorkflowSnapshotMeta, query)
        if page_size:
            query = query.limit(page_size)
        if offset:
            query = query.offset(offset)
        return query.all()

    def delete_workflow_snapshot(self, snapshot_id):
        try:
            self.session.query(WorkflowSnapshotMeta).filter(WorkflowSnapshotMeta.id == snapshot_id).delete()
        except Exception as e:
            self.session.rollback()
            raise e

    # end workflow snapshot

    # begin workflow schedule
    def add_workflow_schedule(self, workflow_id, expression) -> WorkflowScheduleMeta:
        try:
            workflow_schedule_meta = WorkflowScheduleMeta(workflow_id=workflow_id,
                                                          expression=expression)
            self.session.add(workflow_schedule_meta)
            self.session.commit()
            return workflow_schedule_meta
        except Exception as e:
            self.session.rollback()
            raise e

    def get_workflow_schedule(self, schedule_id) -> WorkflowScheduleMeta:
        return self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.id == schedule_id).first()

    def pause_workflow_schedule(self, schedule_id) -> WorkflowScheduleMeta:
        try:
            meta = self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.id == schedule_id).one()
            meta.is_paused = True
            self.session.merge(meta)
            return meta
        except Exception as e:
            self.session.rollback()
            raise e

    def resume_workflow_schedule(self, schedule_id) -> WorkflowScheduleMeta:
        try:
            meta = self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.id == schedule_id).one()
            meta.is_paused = False
            self.session.merge(meta)
            return meta
        except Exception as e:
            self.session.rollback()
            raise e

    def list_workflow_schedules(self, workflow_id) -> List[WorkflowScheduleMeta]:
        return self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.workflow_id == workflow_id).all()

    def delete_workflow_schedule(self, schedule_id):
        try:
            self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.id == schedule_id).delete()
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    # end workflow schedule

    # begin workflow trigger

    def add_workflow_trigger(self, workflow_id, rule) -> WorkflowEventTriggerMeta:
        try:
            workflow_trigger_meta = WorkflowEventTriggerMeta(workflow_id=workflow_id,
                                                             rule=rule)
            self.session.add(workflow_trigger_meta)
            self.session.commit()
            return workflow_trigger_meta
        except Exception as e:
            self.session.rollback()
            raise e

    def get_workflow_trigger(self, trigger_id) -> WorkflowEventTriggerMeta:
        return self.session.query(WorkflowEventTriggerMeta) \
            .filter(WorkflowEventTriggerMeta.id == trigger_id).first()

    def pause_workflow_trigger(self, trigger_id) -> WorkflowEventTriggerMeta:
        try:
            meta = self.session.query(WorkflowEventTriggerMeta).filter(WorkflowEventTriggerMeta.id == trigger_id).one()
            meta.is_paused = True
            self.session.merge(meta)
            return meta
        except Exception as e:
            self.session.rollback()
            raise e

    def resume_workflow_trigger(self, trigger_id) -> WorkflowEventTriggerMeta:
        try:
            meta = self.session.query(WorkflowEventTriggerMeta).filter(WorkflowEventTriggerMeta.id == trigger_id).one()
            meta.is_paused = False
            self.session.merge(meta)
            return meta
        except Exception as e:
            self.session.rollback()
            raise e

    def list_workflow_triggers(self, workflow_id) -> List[WorkflowEventTriggerMeta]:
        return self.session.query(WorkflowEventTriggerMeta) \
            .filter(WorkflowEventTriggerMeta.workflow_id == workflow_id).all()

    def delete_workflow_trigger(self, trigger_id):
        try:
            self.session.query(WorkflowEventTriggerMeta).filter(WorkflowEventTriggerMeta.id == trigger_id).delete()
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    # end workflow trigger

    # begin workflow execution
    def add_workflow_execution(self, workflow_id, run_type, snapshot_id) -> WorkflowExecutionMeta:
        try:
            workflow_execution_meta = WorkflowExecutionMeta(workflow_id=workflow_id,
                                                            run_type=run_type,
                                                            snapshot_id=snapshot_id)
            self.session.add(workflow_execution_meta)
            self.session.commit()
            return workflow_execution_meta
        except Exception as e:
            self.session.rollback()
            raise e

    def update_workflow_execution_status(self, workflow_execution_id, status) -> WorkflowExecutionMeta:
        try:
            meta = self.session.query(WorkflowExecutionMeta) \
                .filter(WorkflowExecutionMeta.id == workflow_execution_id).one()
            meta.status = status
            self.session.merge(meta)
            self.session.commit()
            return meta
        except Exception as e:
            self.session.rollback()
            raise e

    def set_workflow_execution_end_date(self, workflow_execution_id, end_date) -> WorkflowExecutionMeta:
        try:
            meta = self.session.query(WorkflowExecutionMeta) \
                .filter(WorkflowExecutionMeta.id == workflow_execution_id).one()
            meta.end_date = end_date
            self.session.merge(meta)
            self.session.commit()
            return meta
        except Exception as e:
            self.session.rollback()
            raise e

    def get_workflow_execution(self, workflow_execution_id) -> WorkflowExecutionMeta:
        return self.session.query(WorkflowExecutionMeta) \
            .filter(WorkflowExecutionMeta.id == workflow_execution_id).first()

    def list_workflow_executions(self,
                                 workflow_id,
                                 page_size=10,
                                 offset=None,
                                 filters: Filters = None,
                                 orders: Orders = None) -> List[WorkflowExecutionMeta]:
        query = self.session.query(WorkflowExecutionMeta).filter(WorkflowExecutionMeta.workflow_id == workflow_id)
        if filters:
            query = filters.apply_all(WorkflowExecutionMeta, query)
        if orders:
            query = orders.apply_all(WorkflowExecutionMeta, query)
        if page_size:
            query = query.limit(page_size)
        if offset:
            query = query.offset(offset)
        return query.all()

    def delete_workflow_execution(self, workflow_execution_id):
        try:
            self.session.query(WorkflowExecutionMeta) \
                .filter(WorkflowExecutionMeta.id == workflow_execution_id).delete()
        except Exception as e:
            self.session.rollback()
            raise e

    # end workflow execution

    # begin task execution

    def add_task_execution(self,
                           workflow_execution_id,
                           task_name) -> TaskExecutionMeta:
        try:
            task_execution = TaskExecutionMeta(workflow_execution_id=workflow_execution_id, task_name=task_name)
            task_execution.begin_date = utcnow()
            task_execution.status = TaskStatus.INIT.value
            seq = self.session.query(TaskExecutionMeta.sequence_number) \
                .filter(TaskExecutionMeta.workflow_execution_id == workflow_execution_id,
                        TaskExecutionMeta.task_name == task_name).first()
            if seq is None:
                seq = 0
            task_execution.sequence_number = seq + 1
            task_execution.try_number = 1
            self.session.add(task_execution)
            self.session.commit()
            return task_execution
        except Exception as e:
            self.session.rollback()
            raise e

    def update_task_execution(self,
                              task_execution_id,
                              try_number=None,
                              status=None,
                              end_date=None) -> TaskExecutionMeta:
        try:
            meta = self.session.query(TaskExecutionMeta) \
                .filter(TaskExecutionMeta.id == task_execution_id).one()
            if try_number is not None:
                meta.try_number = try_number
            if status is not None:
                meta.status = status
            if end_date is not None:
                meta.end_date = end_date
            return meta
        except Exception as e:
            self.session.rollback()
            raise e

    def get_task_execution(self, task_execution_id) -> TaskExecutionMeta:
        return self.session.query(TaskExecutionMeta) \
            .filter(TaskExecutionMeta.id == task_execution_id).first()

    def list_task_executions(self,
                             workflow_execution_id,
                             page_size=10,
                             offset=None,
                             filters: Filters = None,
                             orders: Orders = None) -> List[TaskExecutionMeta]:
        query = self.session.query(TaskExecutionMeta) \
            .filter(TaskExecutionMeta.workflow_execution_id == workflow_execution_id)
        if filters:
            query = filters.apply_all(TaskExecutionMeta, query)
        if orders:
            query = orders.apply_all(TaskExecutionMeta, query)
        if page_size:
            query = query.limit(page_size)
        if offset:
            query = query.offset(offset)
        return query.all()

    def delete_task_execution(self, task_execution_id):
        try:
            self.session.query(TaskExecutionMeta) \
                .filter(TaskExecutionMeta.id == task_execution_id).delete()
        except Exception as e:
            self.session.rollback()
            raise e

    # end task execution

    # begin event offset
    def set_workflow_event_offset(self, workflow_id, event_offset):
        """Do not committed"""
        meta = self.session.query(WorkflowMeta).filter(WorkflowMeta.id == workflow_id).one()
        meta.event_offset = event_offset
        self.session.merge(meta)

    def get_workflow_event_offset(self, workflow_id) -> int:
        return self.session.query(WorkflowMeta.event_offset).filter(WorkflowMeta.id == workflow_id).first()[0]

    def set_workflow_execution_event_offset(self, workflow_execution_id, event_offset):
        """Do not committed"""
        meta = self.session.query(WorkflowExecutionMeta) \
            .filter(WorkflowExecutionMeta.id == workflow_execution_id).one()
        meta.event_offset = event_offset
        self.session.merge(meta)

    def get_workflow_execution_event_offset(self, workflow_execution_id) -> int:
        return self.session.query(WorkflowExecutionMeta.event_offset) \
            .filter(WorkflowExecutionMeta.id == workflow_execution_id).first()[0]

    # end event offset

    # begin state
    def retrieve_workflow_state(self, workflow_id: int, descriptor: StateDescriptor) -> State:
        if isinstance(descriptor, ValueStateDescriptor):
            return DBWorkflowValueState(session=self.session, workflow_id=workflow_id, state_name=descriptor.name)
        else:
            raise AIFlowException("Now AIFlow only support value state.")

    def create_workflow_state(self, workflow_id: int, descriptor: StateDescriptor) -> State:
        return self.retrieve_workflow_state(workflow_id=workflow_id, descriptor=descriptor)

    def retrieve_workflow_execution_state(self, workflow_execution_id: int, descriptor: StateDescriptor) -> State:
        if isinstance(descriptor, ValueStateDescriptor):
            return DBWorkflowExecutionValueState(session=self.session,
                                                 workflow_execution_id=workflow_execution_id,
                                                 state_name=descriptor.name)
        else:
            raise AIFlowException("Now AIFlow only support value state.")

    def create_workflow_execution_state(self, workflow_execution_id: int, descriptor: StateDescriptor) -> State:
        return self.retrieve_workflow_execution_state(workflow_execution_id=workflow_execution_id,
                                                      descriptor=descriptor)
    # end state
