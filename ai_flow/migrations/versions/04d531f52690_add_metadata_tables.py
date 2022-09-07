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

"""add metadata tables

Revision ID: 04d531f52690
Revises: 
Create Date: 2022-05-12 09:48:33.122155

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04d531f52690'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('namespace',
                    sa.Column('name', sa.String(length=256), nullable=False),
                    sa.Column('properties', sa.String(length=1024), nullable=True),
                    sa.PrimaryKeyConstraint('name'),
                    )
    op.execute("INSERT INTO namespace VALUES ('default', '{}')")
    op.create_table('workflow',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('name', sa.String(length=256), nullable=False),
                    sa.Column('namespace', sa.String(length=256), nullable=False),
                    sa.Column('content', sa.Text(), nullable=False),
                    sa.Column('workflow_object', sa.LargeBinary(), nullable=False),
                    sa.Column('create_time', sa.DateTime(), nullable=True),
                    sa.Column('update_time', sa.DateTime(), nullable=True),
                    sa.Column('is_enabled', sa.Boolean(), nullable=True),
                    sa.Column('event_offset', sa.BigInteger(), nullable=True),
                    sa.ForeignKeyConstraint(['namespace'], ['namespace.name'], ondelete='cascade'),
                    sa.UniqueConstraint('namespace', 'name', name='uq_namespace_name'),
                    sa.PrimaryKeyConstraint('id'),
                    sqlite_autoincrement=True
                    )
    op.create_table('workflow_snapshot',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('workflow_id', sa.Integer(), nullable=False),
                    sa.Column('create_time', sa.DateTime(), nullable=True),
                    sa.Column('workflow_object', sa.LargeBinary(), nullable=False),
                    sa.Column('uri', sa.String(length=1024), nullable=True),
                    sa.Column('signature', sa.String(length=256), nullable=True),
                    sa.ForeignKeyConstraint(['workflow_id'], ['workflow.id'], ondelete='cascade'),
                    sa.PrimaryKeyConstraint('id'),
                    sqlite_autoincrement=True
                    )
    op.create_table('workflow_schedule',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('workflow_id', sa.Integer(), nullable=False),
                    sa.Column('expression', sa.String(length=256), nullable=False),
                    sa.Column('create_time', sa.DateTime(), nullable=True),
                    sa.Column('is_paused', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['workflow_id'], ['workflow.id'], ondelete='cascade'),
                    sa.PrimaryKeyConstraint('id'),
                    sqlite_autoincrement=True
                    )
    op.create_table('workflow_event_trigger',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('workflow_id', sa.Integer(), nullable=False),
                    sa.Column('rule', sa.LargeBinary(), nullable=False),
                    sa.Column('create_time', sa.DateTime(), nullable=True),
                    sa.Column('is_paused', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['workflow_id'], ['workflow.id'], ondelete='cascade'),
                    sa.PrimaryKeyConstraint('id'),
                    sqlite_autoincrement=True
                    )
    op.create_table('workflow_execution',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('workflow_id', sa.Integer(), nullable=False),
                    sa.Column('snapshot_id', sa.Integer(), nullable=False),
                    sa.Column('begin_date', sa.DateTime(), nullable=True),
                    sa.Column('end_date', sa.DateTime(), nullable=True),
                    sa.Column('status', sa.String(length=256), nullable=True),
                    sa.Column('run_type', sa.String(length=256), nullable=True),
                    sa.Column('event_offset', sa.BigInteger(), nullable=True),
                    sa.ForeignKeyConstraint(['workflow_id'],
                                            ['workflow.id'], ondelete='cascade'),
                    sa.ForeignKeyConstraint(['snapshot_id'],
                                            ['workflow_snapshot.id'], onupdate='cascade'),
                    sa.PrimaryKeyConstraint('id'),
                    sqlite_autoincrement=True
                    )
    op.create_table('task_execution',
                    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('workflow_execution_id', sa.Integer(), nullable=False),
                    sa.Column('task_name', sa.String(length=256), nullable=False),
                    sa.Column('sequence_number', sa.Integer(), nullable=False),
                    sa.Column('try_number', sa.Integer(), nullable=False, default=0),
                    sa.Column('begin_date', sa.DateTime(), nullable=True),
                    sa.Column('end_date', sa.DateTime(), nullable=True),
                    sa.Column('status', sa.String(length=256), nullable=True),
                    sa.ForeignKeyConstraint(['workflow_execution_id'],
                                            ['workflow_execution.id'], ondelete='cascade'),
                    sa.PrimaryKeyConstraint('id'),
                    sqlite_autoincrement=True
                    )
    op.create_table('workflow_state',
                    sa.Column('workflow_id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=256), nullable=False),
                    sa.Column('type', sa.String(length=256), nullable=False),
                    sa.Column('value', sa.LargeBinary(), nullable=True),
                    sa.ForeignKeyConstraint(['workflow_id'], ['workflow.id'], ondelete='cascade'),
                    sa.PrimaryKeyConstraint('workflow_id', 'name'),
                    sqlite_autoincrement=True
                    )
    op.create_table('workflow_execution_state',
                    sa.Column('workflow_execution_id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=256), nullable=False),
                    sa.Column('type', sa.String(length=256), nullable=False),
                    sa.Column('value', sa.LargeBinary(), nullable=True),
                    sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_execution.id'], ondelete='cascade'),
                    sa.PrimaryKeyConstraint('workflow_execution_id', 'name'),
                    sqlite_autoincrement=True
                    )


def downgrade():
    op.drop_table('workflow_state')
    op.drop_table('workflow_execution_state')
    op.drop_table('task_execution')
    op.drop_table('workflow_execution')
    op.drop_table('workflow_event_trigger')
    op.drop_table('workflow_schedule')
    op.drop_table('workflow_snapshot')
    op.drop_table('workflow')
    op.drop_table('namespace')
