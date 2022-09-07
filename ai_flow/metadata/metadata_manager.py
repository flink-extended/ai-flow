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
from datetime import datetime
from typing import List, Optional, Tuple, Any

import cloudpickle
from sqlalchemy.sql.functions import count, func

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.metadata.namespace import NamespaceMeta
from ai_flow.metadata.state import DBWorkflowValueState, DBWorkflowExecutionValueState
from ai_flow.metadata.task_execution import TaskExecutionMeta
from ai_flow.metadata.workflow import WorkflowMeta
from ai_flow.metadata.workflow_event_trigger import WorkflowEventTriggerMeta
from ai_flow.metadata.workflow_execution import WorkflowExecutionMeta
from ai_flow.metadata.workflow_schedule import WorkflowScheduleMeta
from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta
from sqlalchemy import asc, desc

from ai_flow.model.operator import OperatorConfigItem
from ai_flow.model.state import StateDescriptor, State, ValueStateDescriptor
from ai_flow.model.status import TaskStatus, TASK_FINISHED_SET, WorkflowStatus, WORKFLOW_FINISHED_SET
from ai_flow.scheduler.timer import timer_instance


class BaseFilter(object):
    """It is the base class of filter conditions for data filtering."""
    column_name = None

    def __init__(self, column_name):
        self.column_name = column_name

    def apply(self, criterion, query, value):
        raise NotImplementedError


class Filters(object):
    """It is a combination of multiple filter conditions."""
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
    """It is the base class of data order."""
    column_name = None

    def __init__(self, column_name):
        self.column_name = column_name

    def apply(self, criterion, query, direction):
        raise NotImplementedError


class Orders(object):
    """It is a combination of multiple order conditions."""

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
    """It represents data retention where the field value is equal to the specified value."""
    def apply(self, criterion, query, value):
        return query.filter(getattr(criterion, self.column_name) == value)


class FilterIn(BaseFilter):
    """It represents data retention where the field value is in the specified list."""
    def apply(self, criterion, query, value):
        return query.filter(getattr(criterion, self.column_name).in_(value))


class OrderBy(BaseOrder):
    """It means that the data is sorted by the value of the specified column."""
    def apply(self, criterion, query, value):
        if value == 'ascend':
            return query.order_by(asc(getattr(criterion, self.column_name)))
        elif value == 'descend':
            return query.order_by(desc(getattr(criterion, self.column_name)))


class MetadataManager(object):
    """It is responsible for managing metadata."""
    def __init__(self, session):
        self.session = session

    def commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def rollback(self):
        self.session.rollback()

    def flush(self):
        self.session.flush()

    # begin namespace
    def add_namespace(self, name, properties) -> NamespaceMeta:
        """
        Add a namespace metadata to MetadataBackend.
        :param name: The name of the namespace.
        :param properties: The properties of the namespace.
        :return: The namespace metadata.
        """
        namespace_meta = NamespaceMeta(name=name, properties=properties)
        self.session.add(namespace_meta)
        self.flush()
        return namespace_meta

    def update_namespace(self, name, properties) -> NamespaceMeta:
        """
        Update the namespace metadata to MetadataBackend.
        :param name: The name of the namespace.
        :param properties: The properties of the namespace.
        :return: The namespace metadata.
        """
        namespace_meta = self.session.query(NamespaceMeta).filter(NamespaceMeta.name == name).one()
        namespace_meta.set_properties(properties)
        self.session.merge(namespace_meta)
        self.flush()
        return namespace_meta

    def delete_namespace(self, name):
        """
        Delete the namespace metadata from MetadataBackend.
        :param name: The name of the namespace.
        """
        self.session.query(NamespaceMeta).filter(NamespaceMeta.name == name).delete()
        self.flush()

    def get_namespace(self, name) -> NamespaceMeta:
        """
        Get a namespace metadata from MetadataBackend.
        :param name: The name of the namespace.
        :return: The namespace metadata.
        """
        return self.session.query(NamespaceMeta).filter(NamespaceMeta.name == name).first()

    def list_namespace(self,
                       page_size=None,
                       offset=None,
                       filters: Filters = None,
                       orders: Orders = None) -> List[NamespaceMeta]:
        """
        List all namespace metadata from MetadataBackend.
        :param page_size: The number of the results.
        :param offset: The start offset of the results.
        :param filters: The conditions of the results.
        :param orders: The orders of the results.
        :return: The namespace metadata list.
        """
        query = self.session.query(NamespaceMeta)
        if filters:
            query = filters.apply_all(NamespaceMeta, query)
        if orders:
            query = orders.apply_all(NamespaceMeta, query)
        if page_size:
            query = query.limit(page_size)
        if offset:
            query = query.offset(offset)
        return query.all()

    # end namespace

    # begin workflow
    def add_workflow(self, namespace, name, content, workflow_object) -> WorkflowMeta:
        """
        Add a workflow metadata to MetadataBackend.
        :param namespace: The name of the namespace.
        :param name: The name of the workflow.
        :param content: The workflow's source code.
        :param workflow_object: The serialized workflow binary.
        :return: The workflow metadata.
        """
        workflow_meta = WorkflowMeta(namespace=namespace,
                                     name=name,
                                     content=content,
                                     workflow_object=workflow_object)
        self.session.add(workflow_meta)
        self.flush()
        return workflow_meta

    def get_workflow_by_name(self, namespace, name) -> WorkflowMeta:
        """
        Get the workflow metadata from MetadataBackend.
        :param namespace: The name of the namespace.
        :param name: The name of the workflow.
        :return: The workflow metadata.
        """
        return self.session.query(WorkflowMeta).filter(WorkflowMeta.namespace == namespace,
                                                       WorkflowMeta.name == name).first()

    def get_workflow_by_id(self, workflow_id) -> Optional[WorkflowMeta]:
        """
        Get the workflow metadata from MetadataBackend.
        :param workflow_id: The unique id of the workflow.
        :return: The workflow metadata.
        """
        return self.session.query(WorkflowMeta).filter(WorkflowMeta.id == workflow_id).first()

    def list_workflows(self,
                       namespace,
                       page_size=None,
                       offset=None,
                       filters: Filters = None,
                       orders: Orders = None) -> List[WorkflowMeta]:
        """
        List workflow metadata from MetadataBackend.
        :param namespace: The name of the namespace.
        :param page_size: The number of the results.
        :param offset: The start offset of the results.
        :param filters: The conditions of the results.
        :param orders: The orders of the results.
        :return: The workflow metadata list.
        """
        query = self.session.query(WorkflowMeta)
        if namespace:
            query = query.filter(WorkflowMeta.namespace == namespace)
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
        """
        Delete a workflow metadata from MetadataBackend.
        :param namespace: The name of the namespace.
        :param workflow_name: The name of the workflow.
        """
        self.session.query(WorkflowMeta).filter(WorkflowMeta.namespace == namespace,
                                                WorkflowMeta.name == workflow_name).delete()
        self.flush()

    def delete_workflow_by_id(self, workflow_id):
        """
        Delete a workflow metadata from MetadataBackend.
        :param workflow_id: The unique id of the workflow.
        """
        self.session.query(WorkflowMeta).filter(WorkflowMeta.id == workflow_id).delete()
        self.flush()

    def update_workflow(self, namespace, name, content=None, workflow_object=None, is_enabled=None) -> WorkflowMeta:
        """
        Update the workflow metadata to MetadataBackend.
        :param namespace: The name of the namespace.
        :param name: The name of the workflow.
        :param content: The workflow's source code.
        :param workflow_object: The serialized workflow binary.
        :param is_enabled: The workflow can be schedule or not.
        :return: The workflow metadata.
        """
        workflow_meta = self.session.query(WorkflowMeta).filter(WorkflowMeta.namespace == namespace,
                                                                WorkflowMeta.name == name).one()
        # todo maybe create workflow snapshot
        if content is not None:
            workflow_meta.content = content
        if workflow_object is not None:
            workflow_meta.workflow_object = workflow_object
        if is_enabled is not None:
            workflow_meta.is_enabled = is_enabled
        workflow_meta.update_time = datetime.now()
        self.session.merge(workflow_meta)
        self.flush()
        return workflow_meta

    # end workflow

    # begin workflow snapshot
    def add_workflow_snapshot(self, workflow_id, uri, workflow_object, signature) -> WorkflowSnapshotMeta:
        """
        Add a workflow snapshot metadata to MetadataBackend.
        :param workflow_id: The unique id of the workflow.
        :param uri: The address of the workflow snapshot.
        :param workflow_object: The serialized workflow binary.
        :param signature: The signature of the snapshot.
        :return: The workflow snapshot metadata.
        """
        workflow_snapshot_meta = WorkflowSnapshotMeta(workflow_id=workflow_id,
                                                      uri=uri,
                                                      workflow_object=workflow_object,
                                                      signature=signature)
        self.session.add(workflow_snapshot_meta)
        self.flush()
        return workflow_snapshot_meta

    def get_workflow_snapshot(self, snapshot_id) -> WorkflowSnapshotMeta:
        """
        Get the workflow snapshot metadata from MetadataBackend.
        :param snapshot_id: The unique id of the workflow snapshot.
        :return: The workflow snapshot metadata.
        """
        return self.session.query(WorkflowSnapshotMeta).filter(WorkflowSnapshotMeta.id == snapshot_id).first()

    def list_workflow_snapshots(self,
                                workflow_id,
                                page_size=None,
                                offset=None,
                                filters: Filters = None,
                                orders: Orders = None) -> List[WorkflowSnapshotMeta]:
        """
        List workflow snapshot metadata from MetadataBackend.
        :param workflow_id: The unique id of the workflow.
        :param page_size: The number of the results.
        :param offset: The start offset of the results.
        :param filters: The conditions of the results.
        :param orders: The orders of the results.
        :return: The workflow snapshot metadata list.
        """
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

    def get_latest_snapshot(self, workflow_id: int) -> WorkflowSnapshotMeta:
        """Get the latest snapshot by workflow_id"""
        return self.session.query(WorkflowSnapshotMeta)\
            .filter(WorkflowSnapshotMeta.workflow_id == workflow_id)\
            .order_by(WorkflowSnapshotMeta.id.desc()).limit(1) \
            .first()

    def delete_workflow_snapshot(self, snapshot_id):
        """
        Delete the workflow snapshot metadata from MetadataBackend.
        :param snapshot_id: The unique id of the workflow snapshot.
        """
        self.session.query(WorkflowSnapshotMeta).filter(WorkflowSnapshotMeta.id == snapshot_id).delete()
        self.flush()

    # end workflow snapshot

    # begin workflow schedule
    def add_workflow_schedule(self, workflow_id, expression) -> WorkflowScheduleMeta:
        """
        Add a workflow schedule metadata to MetadataBackend.
        :param workflow_id: The unique id of the workflow.
        :param expression: The expression of the workflow schedule.
        :return: The workflow schedule metadata.
        """
        workflow_schedule_meta = WorkflowScheduleMeta(workflow_id=workflow_id,
                                                      expression=expression)
        self.session.add(workflow_schedule_meta)
        self.flush()
        timer_instance.add_workflow_schedule_with_session(self.session, workflow_schedule_meta.workflow_id,
                                                          workflow_schedule_meta.id, expression)
        return workflow_schedule_meta

    def get_workflow_schedule(self, schedule_id) -> WorkflowScheduleMeta:
        """
        Get the workflow schedule metadata from MetadataBackend.
        :param schedule_id: The unique id of the workflow schedule.
        :return: The workflow schedule metadata.
        """
        return self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.id == schedule_id).first()

    def pause_workflow_schedule(self, schedule_id) -> WorkflowScheduleMeta:
        """
        Pause scheduling the workflow by workflow schedule.
        :param schedule_id: The unique id of the workflow schedule.
        :return: The workflow schedule metadata.
        """
        meta = self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.id == schedule_id).one()
        meta.is_paused = True
        self.session.merge(meta)
        timer_instance.pause_workflow_schedule_with_session(self.session, schedule_id)
        self.flush()
        return meta

    def resume_workflow_schedule(self, schedule_id) -> WorkflowScheduleMeta:
        """
        Resume scheduling the workflow by workflow schedule.
        :param schedule_id: The unique id of the workflow schedule.
        :return: The workflow schedule metadata.
        """
        meta = self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.id == schedule_id).one()
        meta.is_paused = False
        self.session.merge(meta)
        timer_instance.resume_workflow_schedule_with_session(self.session, schedule_id)
        self.flush()
        return meta

    def list_workflow_schedules(self,
                                workflow_id,
                                page_size=None,
                                offset=None,
                                filters: Filters = None,
                                orders: Orders = None) -> List[WorkflowScheduleMeta]:
        """
        List all workflow schedule metadata.
        :param workflow_id: The unique id of the workflow.
        :param page_size: The number of the results.
        :param offset: The start offset of the results.
        :param filters: The conditions of the results.
        :param orders: The orders of the results.
        :return: The workflow schedule metadata list.
        """
        query = self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.workflow_id == workflow_id)
        if filters:
            query = filters.apply_all(WorkflowScheduleMeta, query)
        if orders:
            query = orders.apply_all(WorkflowScheduleMeta, query)
        if page_size:
            query = query.limit(page_size)
        if offset:
            query = query.offset(offset)
        return query.all()

    def delete_workflow_schedule(self, schedule_id):
        """
        Delete the workflow schedule metadata from MetadataBackend.
        :param schedule_id: The unique id of the workflow schedule.
        """
        self.session.query(WorkflowScheduleMeta).filter(WorkflowScheduleMeta.id == schedule_id).delete()
        timer_instance.delete_workflow_schedule_with_session(self.session, schedule_id)
        self.flush()

    # end workflow schedule

    # begin workflow trigger

    def add_workflow_trigger(self, workflow_id, rule) -> WorkflowEventTriggerMeta:
        """
        Add a workflow schedule metadata to MetadataBackend.
        :param workflow_id: The unique id of the workflow.
        :param rule: The rule's binary of the workflow trigger.
        :return: The workflow trigger metadata.
        """
        workflow_trigger_meta = WorkflowEventTriggerMeta(workflow_id=workflow_id,
                                                         rule=rule)
        self.session.add(workflow_trigger_meta)
        self.flush()
        return workflow_trigger_meta

    def get_workflow_trigger(self, trigger_id) -> WorkflowEventTriggerMeta:
        """
        Get the workflow trigger metadata from MetadataBackend.
        :param trigger_id: The unique id of the workflow trigger.
        :return: The workflow trigger metadata.
        """
        return self.session.query(WorkflowEventTriggerMeta) \
            .filter(WorkflowEventTriggerMeta.id == trigger_id).first()

    def pause_workflow_trigger(self, trigger_id) -> WorkflowEventTriggerMeta:
        """
        Pause scheduling the workflow by workflow trigger.
        :param trigger_id: The unique id of the workflow trigger.
        :return: The workflow trigger metadata.
        """
        meta = self.session.query(WorkflowEventTriggerMeta).filter(WorkflowEventTriggerMeta.id == trigger_id).one()
        meta.is_paused = True
        self.session.merge(meta)
        self.flush()
        return meta

    def resume_workflow_trigger(self, trigger_id) -> WorkflowEventTriggerMeta:
        """
        Resume scheduling the workflow by workflow trigger.
        :param trigger_id: The unique id of the workflow trigger.
        :return: The workflow trigger metadata.
        """
        meta = self.session.query(WorkflowEventTriggerMeta).filter(WorkflowEventTriggerMeta.id == trigger_id).one()
        meta.is_paused = False
        self.session.merge(meta)
        self.flush()
        return meta

    def list_workflow_triggers(self,
                               workflow_id,
                               page_size=None,
                               offset=None,
                               filters: Filters = None,
                               orders: Orders = None
                               ) -> List[WorkflowEventTriggerMeta]:
        """
        List all workflow trigger metadata.
        :param workflow_id: The unique id of the workflow.
        :param page_size: The number of the results.
        :param offset: The start offset of the results.
        :param filters: The conditions of the results.
        :param orders: The orders of the results.
        :return: The workflow trigger metadata list.
        """
        query = self.session.query(WorkflowEventTriggerMeta) \
            .filter(WorkflowEventTriggerMeta.workflow_id == workflow_id)
        if filters:
            query = filters.apply_all(WorkflowEventTriggerMeta, query)
        if orders:
            query = orders.apply_all(WorkflowEventTriggerMeta, query)
        if page_size:
            query = query.limit(page_size)
        if offset:
            query = query.offset(offset)
        return query.all()

    def delete_workflow_trigger(self, trigger_id):
        """
        Delete the workflow trigger metadata from MetadataBackend.
        :param trigger_id: The unique id of the workflow trigger.
        """
        self.session.query(WorkflowEventTriggerMeta).filter(WorkflowEventTriggerMeta.id == trigger_id).delete()
        self.flush()

    def list_all_workflow_triggers(self,
                                   page_size=None,
                                   offset=None,
                                   filters: Filters = None,
                                   orders: Orders = None
                                   ) -> List[WorkflowEventTriggerMeta]:
        """
        List all workflow trigger metadata.
        :return: The workflow trigger metadata list.
        """
        query = self.session.query(WorkflowEventTriggerMeta)
        if filters:
            query = filters.apply_all(WorkflowEventTriggerMeta, query)
        if orders:
            query = orders.apply_all(WorkflowEventTriggerMeta, query)
        if page_size:
            query = query.limit(page_size)
        if offset:
            query = query.offset(offset)
        return query.all()

    # end workflow trigger

    # begin workflow execution
    def add_workflow_execution(self, workflow_id, run_type, snapshot_id) -> WorkflowExecutionMeta:
        """
        Add a workflow execution metadata to MetadataBackend.
        :param workflow_id: The unique id of the workflow.
        :param run_type: The run type(ExecutionType) of the workflow execution.
        :param snapshot_id: The unique id of the workflow snapshot.
        :return: The workflow execution metadata.
        """
        workflow_execution_meta = WorkflowExecutionMeta(workflow_id=workflow_id,
                                                        run_type=run_type,
                                                        snapshot_id=snapshot_id)
        self.session.add(workflow_execution_meta)
        self.flush()
        return workflow_execution_meta

    def update_workflow_execution(self, workflow_execution_id, status=None) -> WorkflowExecutionMeta:
        """
        Update the workflow execution's status metadata to MetadataBackend.
        :param workflow_execution_id: The unique id of the workflow execution.
        :param status: The status(WorkflowStatus) of the workflow execution.
        :return: The workflow execution metadata.
        """
        meta = self.session.query(WorkflowExecutionMeta) \
            .filter(WorkflowExecutionMeta.id == workflow_execution_id).one()
        if status is not None:
            meta.status = status

        workflow = cloudpickle.loads(meta.workflow_snapshot.workflow_object)
        if WorkflowStatus(status) == WorkflowStatus.RUNNING:
            meta.begin_date = datetime.now()
            for task_name, task in workflow.tasks.items():
                if OperatorConfigItem.PERIODIC_EXPRESSION in task.config \
                        and task.config[OperatorConfigItem.PERIODIC_EXPRESSION] is not None:
                    timer_instance.add_task_schedule_with_session(
                        self.session, meta.id, task_name, task.config[OperatorConfigItem.PERIODIC_EXPRESSION])
        elif WorkflowStatus(status) in WORKFLOW_FINISHED_SET:
            meta.end_date = datetime.now()
            for task_name, task in workflow.tasks.items():
                if OperatorConfigItem.PERIODIC_EXPRESSION in task.config \
                        and task.config[OperatorConfigItem.PERIODIC_EXPRESSION] is not None:
                    timer_instance.delete_task_schedule_with_session(self.session, meta.id, task_name)
        self.session.merge(meta)
        self.flush()
        return meta

    def get_workflow_execution(self, workflow_execution_id) -> WorkflowExecutionMeta:
        """
        Get the workflow execution metadata to MetadataBackend.
        :param workflow_execution_id: The unique id of the workflow execution.
        :return: The workflow execution metadata.
        """
        return self.session.query(WorkflowExecutionMeta) \
            .filter(WorkflowExecutionMeta.id == workflow_execution_id).first()

    def list_workflow_executions(self,
                                 workflow_id,
                                 page_size=None,
                                 offset=None,
                                 filters: Filters = None,
                                 orders: Orders = None) -> List[WorkflowExecutionMeta]:
        """
        List workflow execution metadata from MetadataBackend.
        :param workflow_id: The unique id of the workflow.
        :param page_size: The number of the results.
        :param offset: The start offset of the results.
        :param filters: The conditions of the results.
        :param orders: The orders of the results.
        :return: The workflow execution metadata list.
        """
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
        """
        Delete the workflow execution metadata from MetadataBackend.
        :param workflow_execution_id: The unique id of the workflow execution.
        """
        self.session.query(WorkflowExecutionMeta) \
            .filter(WorkflowExecutionMeta.id == workflow_execution_id).delete()
        self.flush()

    # end workflow execution

    # begin task execution

    def add_task_execution(self,
                           workflow_execution_id,
                           task_name) -> TaskExecutionMeta:
        """
        Add a task execution metadata to MetadataBackend.
        :param workflow_execution_id: The unique id of the workflow execution.
        :param task_name: The name of the task.
        :return: The task execution metadata.
        """
        task_execution = TaskExecutionMeta(workflow_execution_id=workflow_execution_id, task_name=task_name)
        task_execution.begin_date = datetime.now()
        task_execution.status = TaskStatus.INIT.value
        seq = self.get_latest_sequence_number(workflow_execution_id=workflow_execution_id, task_name=task_name)
        task_execution.sequence_number = seq + 1
        task_execution.try_number = 1
        self.session.add(task_execution)
        self.flush()
        return task_execution

    def get_latest_sequence_number(self, workflow_execution_id, task_name) -> int:
        """Get the latest task execution's sequence number."""
        task_execution_count = self.session.query(count(TaskExecutionMeta.id)) \
            .filter(TaskExecutionMeta.workflow_execution_id == workflow_execution_id,
                    TaskExecutionMeta.task_name == task_name).scalar()
        return task_execution_count

    def get_latest_task_execution(self, workflow_execution_id, task_name) -> Optional[TaskExecutionMeta]:
        """Get the latest task execution's sequence number."""
        task_execution = self.session.query(TaskExecutionMeta) \
            .filter(TaskExecutionMeta.workflow_execution_id == workflow_execution_id,
                    TaskExecutionMeta.task_name == task_name)\
            .order_by(TaskExecutionMeta.sequence_number.desc())\
            .limit(1)\
            .first()
        return task_execution

    def update_task_execution(self,
                              task_execution_id,
                              try_number=None,
                              status=None) -> TaskExecutionMeta:
        """
        Update the task execution metadata to MetadataBackend.
        :param task_execution_id: The unique id of the task execution.
        :param try_number: The run number of the task execution.
        :param status: The status(TaskStatus) of the task execution.
        :return: The task execution metadata.
        """
        meta = self.session.query(TaskExecutionMeta) \
            .filter(TaskExecutionMeta.id == task_execution_id).one()
        if try_number is not None:
            meta.try_number = try_number
        if status is not None:
            meta.status = status
            if TaskStatus(status) in TASK_FINISHED_SET:
                meta.end_date = datetime.now()
        self.session.merge(meta)
        self.flush()
        return meta

    def get_task_execution_by_id(self, task_execution_id) -> TaskExecutionMeta:
        """
        Get the task execution metadata from MetadataBackend.
        :param task_execution_id: The unique id of the task execution.
        :return: The task execution metadata.
        """
        return self.session.query(TaskExecutionMeta) \
            .filter(TaskExecutionMeta.id == task_execution_id).first()

    def get_task_execution(self, workflow_execution_id, task_name, sequence_number) -> TaskExecutionMeta:
        """
        Get the task execution metadata from MetadataBackend.
        :param workflow_execution_id: The unique id of the workflow execution.
        :param task_name: The name of the task.
        :param sequence_number: The task execution's sequence number.
        :return: The task execution metadata.
        """
        return self.session.query(TaskExecutionMeta) \
            .filter(TaskExecutionMeta.workflow_execution_id == workflow_execution_id,
                    TaskExecutionMeta.task_name == task_name,
                    TaskExecutionMeta.sequence_number == sequence_number).first()

    def list_task_executions(self,
                             workflow_execution_id,
                             page_size=None,
                             offset=None,
                             filters: Filters = None,
                             orders: Orders = None) -> List[TaskExecutionMeta]:
        """
        List task execution metadata from MetadataBackend.
        :param workflow_execution_id: The unique id of the workflow execution.
        :param page_size: The number of the results.
        :param offset: The start offset of the results.
        :param filters: The conditions of the results.
        :param orders: The orders of the results.
        :return: The task execution metadata list.
        """
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
        """
        Delete the task execution metadata from MetadataBackend.
        :param task_execution_id: The unique id of the task execution.
        """
        self.session.query(TaskExecutionMeta).filter(TaskExecutionMeta.id == task_execution_id).delete()
        self.flush()

    # end task execution

    # begin event offset
    def set_workflow_event_offset(self, workflow_id, event_offset):
        """
        Set the event offset for the workflow(Do not committed).
        :param workflow_id: The unique id of the workflow.
        :param event_offset: The event offset for the workflow.
        """
        meta = self.session.query(WorkflowMeta).filter(WorkflowMeta.id == workflow_id).one()
        meta.event_offset = event_offset
        self.session.merge(meta)
        self.flush()

    def get_workflow_event_offset(self, workflow_id) -> int:
        """
        Get the event offset of the workflow.
        :param workflow_id: The unique id of the workflow.
        :return: The workflow event offset.
        """
        return self.session.query(WorkflowMeta.event_offset).filter(WorkflowMeta.id == workflow_id).first()[0]

    def set_workflow_execution_event_offset(self, workflow_execution_id, event_offset):
        """
        Set the event offset for the workflow execution(Do not committed).
        :param workflow_execution_id: The unique id of the workflow execution.
        :param event_offset: The event offset for the workflow execution.
        """
        meta = self.session.query(WorkflowExecutionMeta) \
            .filter(WorkflowExecutionMeta.id == workflow_execution_id).one()
        meta.event_offset = event_offset
        self.session.merge(meta)
        self.flush()

    def get_workflow_execution_event_offset(self, workflow_execution_id) -> int:
        """
        Get the event offset of the workflow execution.
        :param workflow_execution_id: The unique id of the workflow execution.
        :return: The workflow execution event offset.
        """
        return self.session.query(WorkflowExecutionMeta.event_offset) \
            .filter(WorkflowExecutionMeta.id == workflow_execution_id).first()[0]

    # end event offset

    # begin state
    def get_or_create_workflow_state(self, workflow_id: int, descriptor: StateDescriptor) -> State:
        """
        Get or create a workflow state.
        :param workflow_id: The unique id of the workflow.
        :param descriptor: The descriptor of the workflow state.
        :return: The workflow state.
        """
        if isinstance(descriptor, ValueStateDescriptor):
            return DBWorkflowValueState(session=self.session, workflow_id=workflow_id, state_name=descriptor.name)
        else:
            raise AIFlowException("Now AIFlow only support value state.")

    def get_or_create_workflow_execution_state(self, workflow_execution_id: int, descriptor: StateDescriptor) -> State:
        """
        Get or create a workflow execution state.
        :param workflow_execution_id: The unique id of the workflow execution.
        :param descriptor: The descriptor of the workflow state.
        :return: The workflow execution state.
        """
        if isinstance(descriptor, ValueStateDescriptor):
            return DBWorkflowExecutionValueState(session=self.session,
                                                 workflow_execution_id=workflow_execution_id,
                                                 state_name=descriptor.name)
        else:
            raise AIFlowException("Now AIFlow only support value state.")
    # end state

    def get_max_event_offset_of_workflow(self):
        return self.session.query(func.max(WorkflowMeta.event_offset)).scalar()

    def get_max_event_offset_of_workflow_execution(self):
        return self.session.query(func.max(WorkflowExecutionMeta.event_offset)).scalar()
