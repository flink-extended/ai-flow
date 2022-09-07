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
import os
import unittest
from datetime import datetime

import cloudpickle
from sqlalchemy.exc import IntegrityError

from ai_flow.common.util.db_util.db_migration import init_db
from ai_flow.common.util.db_util.session import new_session
from ai_flow.metadata.metadata_manager import MetadataManager, Filters, FilterEqual, Orders, OrderBy, FilterIn
from ai_flow.model.execution_type import ExecutionType
from ai_flow.operators.bash import BashOperator
from ai_flow.model.state import ValueStateDescriptor, ValueState
from ai_flow.model.status import WorkflowStatus, TaskStatus
from ai_flow.model.workflow import Workflow


class TestMetadataManager(unittest.TestCase):
    def setUp(self) -> None:
        self.file = 'test.db'
        self._delete_db_file()
        self.url = 'sqlite:///{}'.format(self.file)
        init_db(self.url)
        self.session = new_session(db_uri=self.url)
        self.metadata_manager = MetadataManager(session=self.session)

    def _delete_db_file(self):
        if os.path.exists(self.file):
            os.remove(self.file)

    def tearDown(self) -> None:
        self.session.close()
        self._delete_db_file()

    def session_rollback(self):
        self.metadata_manager.rollback()

    def test_default_namespace_already_exists(self):
        with self.assertRaises(IntegrityError):
            self.metadata_manager.add_namespace(name='default', properties={})

    def test_namespace_operations(self):
        namespace_metas = self.metadata_manager.list_namespace()
        self.assertEqual(1, len(namespace_metas))
        self.assertEqual('default', namespace_metas[0].name)

        namespace_meta_1 = self.metadata_manager.add_namespace(name='namespace_1', properties={'a': 'a'})
        self.metadata_manager.commit()
        self.assertEqual('namespace_1', namespace_meta_1.name)
        self.assertEqual('a', namespace_meta_1.get_properties()['a'])
        namespace_meta_1 = self.metadata_manager.update_namespace(name='namespace_1', properties={'a': 'b'})
        self.metadata_manager.commit()
        self.assertEqual('b', namespace_meta_1.get_properties()['a'])
        namespace_meta_1 = self.metadata_manager.get_namespace(name='namespace_1')
        self.assertEqual('b', namespace_meta_1.get_properties()['a'])
        namespace_meta_2 = self.metadata_manager.add_namespace(name='namespace_2', properties={'c': 'c'})
        self.metadata_manager.commit()
        namespace_metas = self.metadata_manager.list_namespace()
        self.assertEqual(3, len(namespace_metas))
        self.metadata_manager.delete_namespace('namespace_1')
        self.metadata_manager.commit()
        namespace_metas = self.metadata_manager.list_namespace()
        self.assertEqual(2, len(namespace_metas))
        self.metadata_manager.delete_namespace('namespace_2')
        self.metadata_manager.commit()
        namespace_metas = self.metadata_manager.list_namespace()
        self.assertEqual(1, len(namespace_metas))

    def test_add_workflow_without_namespace(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        workflow_object = cloudpickle.dumps(content)

        with self.assertRaises(Exception) as context:
            workflow_meta_1 = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                                 name='workflow_1',
                                                                 content=content,
                                                                 workflow_object=workflow_object)
            self.metadata_manager.commit()
        self.assertTrue('constraint failed' in str(context.exception))

    def test_add_update_delete_workflows(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        workflow_object = cloudpickle.dumps(content)
        namespace_meta = self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})

        workflow_meta = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                           name='workflow_1',
                                                           content=content,
                                                           workflow_object=workflow_object)
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.get_workflow_by_id(workflow_meta.id)
        update_time_1 = workflow_meta.update_time
        self.metadata_manager.update_workflow(namespace=namespace_name,
                                              name='workflow_1',
                                              is_enabled=False)
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.get_workflow_by_id(workflow_meta.id)
        update_time_2 = workflow_meta.update_time
        self.assertEqual(False, workflow_meta.is_enabled)
        self.assertEqual(workflow_meta.create_time, workflow_meta.create_time)
        self.assertLess(update_time_1, update_time_2)

        self.metadata_manager.delete_workflow_by_id(workflow_meta.id)
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.get_workflow_by_id(workflow_meta.id)
        self.assertEqual(None, workflow_meta)
        workflow_meta = self.metadata_manager.get_workflow_by_name(namespace=namespace_name, name='workflow_1')
        self.assertEqual(None, workflow_meta)

    def test_get_and_list_workflows(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        workflow_object = cloudpickle.dumps(content)
        namespace_meta = self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})

        workflow_meta_1 = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                             name='workflow_1',
                                                             content=content,
                                                             workflow_object=workflow_object)
        self.metadata_manager.commit()
        workflow_meta_1_1 = self.metadata_manager.get_workflow_by_id(workflow_meta_1.id)
        self.assertEqual(workflow_meta_1.name, workflow_meta_1_1.name)
        self.assertEqual(namespace_name, workflow_meta_1_1.namespace)

        workflow_meta_2 = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                             name='workflow_2',
                                                             content=content,
                                                             workflow_object=workflow_object)
        self.metadata_manager.commit()

        workflow_metas = self.metadata_manager.list_workflows(namespace=namespace_name)
        self.assertEqual(2, len(workflow_metas))
        workflow_metas = self.metadata_manager.list_workflows(namespace=namespace_name, page_size=1)
        self.assertEqual(1, len(workflow_metas))
        workflow_metas = self.metadata_manager.list_workflows(namespace=namespace_name, offset=1)
        self.assertEqual(1, len(workflow_metas))
        workflow_metas = self.metadata_manager.list_workflows(namespace=namespace_name,
                                                              filters=Filters(
                                                                  filters=[(FilterEqual('name'), 'workflow_1')]))
        self.assertEqual(1, len(workflow_metas))
        self.assertEqual('workflow_1', workflow_metas[0].name)

        workflow_metas = self.metadata_manager.list_workflows(namespace=namespace_name,
                                                              filters=Filters(
                                                                  filters=[(FilterIn('name'),
                                                                            ['workflow_1', 'workflow_2'])]))
        self.assertEqual(2, len(workflow_metas))
        self.assertTrue(workflow_metas[0].name in {'workflow_1', 'workflow_2'})
        self.assertTrue(workflow_metas[1].name in {'workflow_1', 'workflow_2'})

        workflow_metas = self.metadata_manager.list_workflows(namespace=namespace_name,
                                                              orders=Orders(orders=[(OrderBy('id'), 'ascend')]))
        self.assertEqual(2, len(workflow_metas))
        self.assertEqual('workflow_1', workflow_metas[0].name)

        workflow_metas = self.metadata_manager.list_workflows(namespace=namespace_name,
                                                              orders=Orders(orders=[(OrderBy('id'), 'descend')]))
        self.assertEqual(2, len(workflow_metas))
        self.assertEqual('workflow_2', workflow_metas[0].name)

    def test_workflow_snapshot_operations(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        workflow_object = cloudpickle.dumps(content)
        namespace_meta = self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})

        workflow_meta = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                           name='workflow',
                                                           content=content,
                                                           workflow_object=workflow_object)
        self.metadata_manager.commit()
        snapshot_meta = self.metadata_manager.get_latest_snapshot(workflow_id=workflow_meta.id)
        self.assertIsNone(snapshot_meta)

        for i in range(3):
            snapshot_meta = self.metadata_manager.add_workflow_snapshot(workflow_id=workflow_meta.id,
                                                                        workflow_object=workflow_meta.workflow_object,
                                                                        uri='url',
                                                                        signature=str(i))
        self.metadata_manager.commit()

        snapshot_meta = self.metadata_manager.get_workflow_snapshot(1)
        self.assertEqual('0', snapshot_meta.signature)
        snapshot_metas = self.metadata_manager.list_workflow_snapshots(workflow_id=workflow_meta.id)
        self.assertEqual(3, len(snapshot_metas))

        self.metadata_manager.delete_workflow_snapshot(1)
        snapshot_metas = self.metadata_manager.list_workflow_snapshots(workflow_id=workflow_meta.id)
        self.assertEqual(2, len(snapshot_metas))
        snapshot_meta = self.metadata_manager.get_latest_snapshot(workflow_id=workflow_meta.id)
        self.assertEqual(3, snapshot_meta.id)

    def test_workflow_schedule_operations(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        with Workflow(name='workflow') as workflow:
            BashOperator(name='bash1', bash_command='echo 1')
        workflow_object = cloudpickle.dumps(workflow)
        namespace_meta = self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                           name='workflow',
                                                           content=content,
                                                           workflow_object=workflow_object)
        self.metadata_manager.commit()
        for i in range(3):
            self.metadata_manager.add_workflow_schedule(workflow_id=workflow_meta.id,
                                                        expression='cron@*/1 * * * *')
            self.metadata_manager.commit()
        meta = self.metadata_manager.get_workflow_schedule(1)
        self.assertEqual('cron@*/1 * * * *', meta.expression)
        metas = self.metadata_manager.list_workflow_schedules(workflow_id=workflow_meta.id)
        self.assertEqual(3, len(metas))

        self.metadata_manager.delete_workflow_schedule(1)
        self.metadata_manager.commit()
        metas = self.metadata_manager.list_workflow_schedules(workflow_id=workflow_meta.id)
        self.assertEqual(2, len(metas))

        self.metadata_manager.pause_workflow_schedule(2)
        self.metadata_manager.commit()
        meta = self.metadata_manager.get_workflow_schedule(2)
        self.assertTrue(meta.is_paused)

        self.metadata_manager.resume_workflow_schedule(2)
        self.metadata_manager.commit()
        meta = self.metadata_manager.get_workflow_schedule(2)
        self.assertFalse(meta.is_paused)

    def test_workflow_trigger_operations(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        workflow_object = cloudpickle.dumps(content)
        namespace_meta = self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                           name='workflow',
                                                           content=content,
                                                           workflow_object=workflow_object)
        self.metadata_manager.commit()
        for i in range(3):
            self.metadata_manager.add_workflow_trigger(workflow_id=workflow_meta.id,
                                                       rule=bytes(str(i), 'UTF-8'))
            self.metadata_manager.commit()
        meta = self.metadata_manager.get_workflow_trigger(1)
        self.assertEqual('0', meta.rule.decode("utf-8"))
        metas = self.metadata_manager.list_workflow_triggers(workflow_id=workflow_meta.id)
        self.assertEqual(3, len(metas))

        self.metadata_manager.delete_workflow_trigger(1)
        self.metadata_manager.commit()
        metas = self.metadata_manager.list_workflow_triggers(workflow_id=workflow_meta.id)
        self.assertEqual(2, len(metas))

        self.metadata_manager.pause_workflow_trigger(2)
        self.metadata_manager.commit()
        meta = self.metadata_manager.get_workflow_trigger(2)
        self.assertTrue(meta.is_paused)

        self.metadata_manager.resume_workflow_trigger(2)
        self.metadata_manager.commit()
        meta = self.metadata_manager.get_workflow_trigger(2)
        self.assertFalse(meta.is_paused)

    def test_workflow_execution_operations(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        with Workflow(name='workflow') as workflow:
            BashOperator(name='bash1', bash_command='echo 1')
        workflow_object = cloudpickle.dumps(workflow)
        namespace_meta = self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                           name='workflow',
                                                           content=content,
                                                           workflow_object=workflow_object)
        self.metadata_manager.commit()
        with self.assertRaises(Exception) as context:
            self.metadata_manager.add_workflow_execution(workflow_id=workflow_meta.id,
                                                         snapshot_id=1,
                                                         run_type=ExecutionType.MANUAL.value)
            self.metadata_manager.commit()
        self.assertTrue('FOREIGN KEY constraint failed' in str(context.exception))
        self.session_rollback()
        snapshot = self.metadata_manager.add_workflow_snapshot(workflow_id=workflow_meta.id,
                                                               workflow_object=workflow_meta.workflow_object,
                                                               uri='url',
                                                               signature='xxx')
        self.metadata_manager.commit()
        for i in range(3):
            self.metadata_manager.add_workflow_execution(workflow_id=workflow_meta.id,
                                                         snapshot_id=snapshot.id,
                                                         run_type=ExecutionType.MANUAL.value)
            self.metadata_manager.commit()
        metas = self.metadata_manager.list_workflow_executions(workflow_id=workflow_meta.id)
        self.assertEqual(3, len(metas))
        meta = self.metadata_manager.get_workflow_execution(workflow_execution_id=metas[0].id)
        self.assertIsNone(meta.end_date)
        meta = self.metadata_manager.get_workflow_execution(workflow_execution_id=meta.id)
        self.assertEqual(WorkflowStatus.INIT.value, meta.status)
        meta = self.metadata_manager.update_workflow_execution(workflow_execution_id=meta.id,
                                                               status=WorkflowStatus.SUCCESS.value)
        self.metadata_manager.commit()
        self.assertIsNotNone(meta.end_date)
        meta = self.metadata_manager.get_workflow_execution(workflow_execution_id=meta.id)
        self.assertEqual(WorkflowStatus.SUCCESS.value, meta.status)
        meta = self.metadata_manager.delete_workflow_execution(workflow_execution_id=meta.id)
        self.metadata_manager.commit()
        metas = self.metadata_manager.list_workflow_executions(workflow_id=workflow_meta.id)
        self.assertEqual(2, len(metas))

    def test_task_execution_operations(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        workflow_object = cloudpickle.dumps(content)
        namespace_meta = self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.add_workflow(namespace=namespace_meta.name,
                                                           name='workflow',
                                                           content=content,
                                                           workflow_object=workflow_object)
        self.metadata_manager.commit()
        snapshot = self.metadata_manager.add_workflow_snapshot(workflow_id=workflow_meta.id,
                                                               workflow_object=workflow_meta.workflow_object,
                                                               uri='url',
                                                               signature='xxx')
        self.metadata_manager.commit()
        with self.assertRaises(Exception) as context:
            self.metadata_manager.add_task_execution(workflow_execution_id=1, task_name='task')
            self.metadata_manager.commit()
        self.assertTrue('FOREIGN KEY constraint failed' in str(context.exception))
        self.session_rollback()
        workflow_execution_meta = self.metadata_manager.add_workflow_execution(workflow_id=workflow_meta.id,
                                                                               snapshot_id=snapshot.id,
                                                                               run_type=ExecutionType.MANUAL.value)
        self.metadata_manager.commit()
        seq_num = self.metadata_manager.get_latest_sequence_number(workflow_execution_id=workflow_execution_meta.id,
                                                                   task_name='task')
        self.assertEqual(0, seq_num)
        for i in range(3):
            self.metadata_manager.add_task_execution(workflow_execution_id=workflow_execution_meta.id,
                                                     task_name='task')
            self.metadata_manager.commit()
        metas = self.metadata_manager.list_task_executions(workflow_execution_id=workflow_execution_meta.id)
        self.assertEqual(3, len(metas))
        seq_num = self.metadata_manager.get_latest_sequence_number(workflow_execution_id=workflow_execution_meta.id,
                                                                   task_name='task')
        self.assertEqual(3, seq_num)
        for i in range(3):
            self.assertEqual(i+1, metas[i].sequence_number)
        meta = self.metadata_manager.get_task_execution_by_id(task_execution_id=metas[0].id)
        self.assertEqual(TaskStatus.INIT.value, meta.status)
        self.assertEqual(1, meta.try_number)

        meta = self.metadata_manager.update_task_execution(task_execution_id=meta.id,
                                                           try_number=2,
                                                           status=TaskStatus.SUCCESS.value)
        self.metadata_manager.commit()
        meta = self.metadata_manager.get_task_execution(workflow_execution_id=meta.workflow_execution_id,
                                                        task_name=meta.task_name,
                                                        sequence_number=meta.sequence_number)
        self.assertEqual(WorkflowStatus.SUCCESS.value, meta.status)
        self.assertEqual(2, meta.try_number)

        meta = self.metadata_manager.delete_task_execution(task_execution_id=meta.id)
        self.metadata_manager.commit()
        metas = self.metadata_manager.list_task_executions(workflow_execution_id=workflow_execution_meta.id)
        self.assertEqual(2, len(metas))

    def test_event_offset_operations(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        workflow_object = cloudpickle.dumps(content)
        namespace_meta = self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})
        self.metadata_manager.commit()

        workflow_meta = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                           name='workflow_1',
                                                           content=content,
                                                           workflow_object=workflow_object)
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.get_workflow_by_id(workflow_meta.id)
        snapshot = self.metadata_manager.add_workflow_snapshot(workflow_id=workflow_meta.id,
                                                               workflow_object=workflow_meta.workflow_object,
                                                               uri='url',
                                                               signature='xxx')
        self.metadata_manager.commit()
        workflow_execution_meta = self.metadata_manager.add_workflow_execution(workflow_id=workflow_meta.id,
                                                                               snapshot_id=snapshot.id,
                                                                               run_type=ExecutionType.MANUAL.value)
        self.metadata_manager.commit()
        offset = self.metadata_manager.get_workflow_event_offset(workflow_id=workflow_meta.id)
        self.assertEqual(-1, offset)
        self.metadata_manager.set_workflow_event_offset(workflow_id=workflow_meta.id, event_offset=5)
        self.metadata_manager.commit()
        offset = self.metadata_manager.get_workflow_event_offset(workflow_id=workflow_meta.id)
        self.assertEqual(5, offset)

        offset = self.metadata_manager.get_workflow_execution_event_offset(
            workflow_execution_id=workflow_execution_meta.id)
        self.assertEqual(-1, offset)
        self.metadata_manager.set_workflow_execution_event_offset(workflow_execution_id=workflow_execution_meta.id,
                                                                  event_offset=5)
        self.metadata_manager.commit()
        offset = self.metadata_manager.get_workflow_execution_event_offset(
            workflow_execution_id=workflow_execution_meta.id)
        self.assertEqual(5, offset)

    def test_state_operations(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        workflow_object = cloudpickle.dumps(content)
        namespace_meta = self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.add_workflow(namespace=namespace_name,
                                                           name='workflow_1',
                                                           content=content,
                                                           workflow_object=workflow_object)
        self.metadata_manager.commit()
        workflow_meta = self.metadata_manager.get_workflow_by_id(workflow_meta.id)
        snapshot = self.metadata_manager.add_workflow_snapshot(workflow_id=workflow_meta.id,
                                                               workflow_object=workflow_meta.workflow_object,
                                                               uri='url',
                                                               signature='xxx')
        self.metadata_manager.commit()
        workflow_execution_meta = self.metadata_manager.add_workflow_execution(workflow_id=workflow_meta.id,
                                                                               snapshot_id=snapshot.id,
                                                                               run_type=ExecutionType.MANUAL.value)
        self.metadata_manager.commit()
        state = self.metadata_manager.get_or_create_workflow_state(workflow_id=workflow_meta.id,
                                                                   descriptor=ValueStateDescriptor(name='s1'))
        self.metadata_manager.commit()
        self.assertTrue(isinstance(state, ValueState))
        self.assertIsNone(state.value())
        state.update('xx')
        self.assertEqual('xx', state.value())

        state = self.metadata_manager.get_or_create_workflow_execution_state(
            workflow_execution_id=workflow_execution_meta.id,
            descriptor=ValueStateDescriptor(name='s1'))
        self.metadata_manager.commit()
        self.assertTrue(isinstance(state, ValueState))
        self.assertIsNone(state.value())
        state.update('xx')
        self.assertEqual('xx', state.value())

    def test_max_event_offset(self):
        namespace_name = 'namespace'
        content = 'source of workflow'
        workflow_object = cloudpickle.dumps(content)
        self.metadata_manager.add_namespace(name=namespace_name, properties={'a': 'a'})
        workflow_meta1 = self.metadata_manager.add_workflow(namespace=namespace_name, name='workflow_1',
                                                            content=content, workflow_object=workflow_object)
        self.metadata_manager.set_workflow_event_offset(workflow_meta1.id, 1)
        snapshot1 = self.metadata_manager.add_workflow_snapshot(
            workflow_id=workflow_meta1.id, workflow_object=workflow_meta1.workflow_object, uri='url', signature='xxx')
        workflow_meta2 = self.metadata_manager.add_workflow(namespace=namespace_name, name='workflow_2',
                                                            content=content, workflow_object=workflow_object)
        self.metadata_manager.set_workflow_event_offset(workflow_meta2.id, 2)
        snapshot2 = self.metadata_manager.add_workflow_snapshot(
            workflow_id=workflow_meta2.id, workflow_object=workflow_meta2.workflow_object, uri='url', signature='xxx')

        execution_meta1 = self.metadata_manager.add_workflow_execution(
            workflow_id=workflow_meta1.id, snapshot_id=snapshot1.id, run_type=ExecutionType.MANUAL.value)
        self.metadata_manager.set_workflow_execution_event_offset(execution_meta1.id, 3)
        execution_meta2 = self.metadata_manager.add_workflow_execution(
            workflow_id=workflow_meta2.id, snapshot_id=snapshot2.id, run_type=ExecutionType.MANUAL.value)
        self.metadata_manager.set_workflow_execution_event_offset(execution_meta2.id, 4)
        self.assertEqual(2, self.metadata_manager.get_max_event_offset_of_workflow())
        self.assertEqual(4, self.metadata_manager.get_max_event_offset_of_workflow_execution())


if __name__ == '__main__':
    unittest.main()
