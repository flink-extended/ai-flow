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

"""add_ai_flow_tables

Revision ID: de1c96ef582a
Revises: 
Create Date: 2021-10-13 16:18:36.091074

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'de1c96ef582a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('artifact',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('artifact_type', sa.String(length=256), nullable=True),
                    sa.Column('description', sa.String(length=1000), nullable=True),
                    sa.Column('uri', sa.String(length=1000), nullable=True),
                    sa.Column('create_time', sa.BigInteger(), nullable=True),
                    sa.Column('update_time', sa.BigInteger(), nullable=True),
                    sa.Column('properties', sa.String(length=1000), nullable=True),
                    sa.Column('is_deleted', sa.String(length=256), nullable=True),
                    sa.PrimaryKeyConstraint('uuid'),
                    sa.UniqueConstraint('name'),
                    sqlite_autoincrement=True
                    )
    op.create_table('dataset',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('format', sa.String(length=256), nullable=True),
                    sa.Column('description', sa.String(length=1000), nullable=True),
                    sa.Column('uri', sa.String(length=1000), nullable=True),
                    sa.Column('create_time', sa.BigInteger(), nullable=True),
                    sa.Column('update_time', sa.BigInteger(), nullable=True),
                    sa.Column('properties', sa.String(length=1000), nullable=True),
                    sa.Column('name_list', sa.String(length=1000), nullable=True),
                    sa.Column('type_list', sa.String(length=1000), nullable=True),
                    sa.Column('catalog_name', sa.String(length=1000), nullable=True),
                    sa.Column('catalog_type', sa.String(length=1000), nullable=True),
                    sa.Column('catalog_database', sa.String(length=1000), nullable=True),
                    sa.Column('catalog_connection_uri', sa.String(length=1000), nullable=True),
                    sa.Column('catalog_table', sa.String(length=1000), nullable=True),
                    sa.Column('is_deleted', sa.String(length=256), nullable=True),
                    sa.PrimaryKeyConstraint('uuid'),
                    sa.UniqueConstraint('name'),
                    sqlite_autoincrement=True
                    )
    op.create_table('event',
                    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('key', sa.String(length=1024), nullable=False),
                    sa.Column('version', sa.Integer(), nullable=False),
                    sa.Column('value', sa.String(length=1024), nullable=True),
                    sa.Column('event_type', sa.String(length=256), nullable=True),
                    sa.Column('create_time', sa.BigInteger(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sqlite_autoincrement=True
                    )
    op.create_table('metric_meta',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('metric_name', sa.String(length=256), nullable=False),
                    sa.Column('metric_type', sa.String(length=256), nullable=True),
                    sa.Column('metric_desc', sa.String(length=4096), nullable=True),
                    sa.Column('project_name', sa.String(length=256), nullable=False),
                    sa.Column('dataset_name', sa.String(length=256), nullable=True),
                    sa.Column('model_name', sa.String(length=256), nullable=True),
                    sa.Column('job_name', sa.String(length=256), nullable=True),
                    sa.Column('start_time', sa.BigInteger(), nullable=True),
                    sa.Column('end_time', sa.BigInteger(), nullable=True),
                    sa.Column('uri', sa.String(length=1024), nullable=True),
                    sa.Column('tags', sa.String(length=256), nullable=True),
                    sa.Column('properties', sa.String(length=1024), nullable=True),
                    sa.Column('is_deleted', sa.String(length=128), nullable=True),
                    sa.PrimaryKeyConstraint('uuid'),
                    sa.UniqueConstraint('metric_name'),
                    sqlite_autoincrement=True
                    )
    op.create_table('project',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('name', sa.String(length=255), nullable=True),
                    sa.Column('properties', sa.String(length=1000), nullable=True),
                    sa.Column('uri', sa.String(length=1000), nullable=True),
                    sa.Column('is_deleted', sa.String(length=256), nullable=True),
                    sa.PrimaryKeyConstraint('uuid'),
                    sa.UniqueConstraint('name'),
                    sqlite_autoincrement=True
                    )
    op.create_table('registered_model',
                    sa.Column('model_name', sa.String(length=255), nullable=False),
                    sa.Column('model_desc', sa.String(length=1000), nullable=True),
                    sa.PrimaryKeyConstraint('model_name', name='registered_model_pk'),
                    sa.UniqueConstraint('model_name')
                    )
    op.create_table('workflow_execution_event_handler_state',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('project_name', sa.String(length=256), nullable=False),
                    sa.Column('workflow_name', sa.String(length=256), nullable=False),
                    sa.Column('context', sa.String(length=256), nullable=False),
                    sa.Column('workflow_execution_id', sa.Text(), nullable=True),
                    sa.Column('state', sa.PickleType(), nullable=True),
                    sa.PrimaryKeyConstraint('uuid'),
                    sa.UniqueConstraint('project_name', 'workflow_name', 'context'),
                    sqlite_autoincrement=True
                    )
    op.create_table('metric_summary',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('metric_name', sa.String(length=256), nullable=False),
                    sa.Column('metric_key', sa.String(length=256), nullable=False),
                    sa.Column('metric_value', sa.String(length=2048), nullable=False),
                    sa.Column('metric_timestamp', sa.BigInteger(), nullable=False),
                    sa.Column('model_version', sa.String(length=256), nullable=True),
                    sa.Column('job_execution_id', sa.String(length=256), nullable=True),
                    sa.Column('is_deleted', sa.String(length=128), nullable=True),
                    sa.ForeignKeyConstraint(['metric_name'], ['metric_meta.metric_name'], onupdate='cascade'),
                    sa.PrimaryKeyConstraint('uuid'),
                    sqlite_autoincrement=True
                    )
    op.create_table('model_relation',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('name', sa.String(length=255), nullable=True),
                    sa.Column('project_id', sa.BigInteger(), nullable=True),
                    sa.Column('is_deleted', sa.String(length=256), nullable=True),
                    sa.ForeignKeyConstraint(['project_id'], ['project.uuid'], onupdate='cascade'),
                    sa.PrimaryKeyConstraint('uuid'),
                    sa.UniqueConstraint('name'),
                    sqlite_autoincrement=True
                    )
    op.create_table('model_version',
                    sa.Column('model_name', sa.String(length=255), nullable=False),
                    sa.Column('model_version', sa.String(length=10), nullable=False),
                    sa.Column('model_path', sa.String(length=500), nullable=True),
                    sa.Column('model_type', sa.String(length=500), nullable=True),
                    sa.Column('version_desc', sa.String(length=1000), nullable=True),
                    sa.Column('version_status', sa.String(length=20), nullable=True),
                    sa.Column('current_stage', sa.String(length=20), nullable=False),
                    sa.ForeignKeyConstraint(['model_name'], ['registered_model.model_name'], onupdate='cascade',
                                            ondelete='cascade'),
                    sa.PrimaryKeyConstraint('model_name', 'model_version', 'current_stage', name='model_version_pk')
                    )
    op.create_table('project_snapshot',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('project_id', sa.BigInteger(), nullable=True),
                    sa.Column('signature', sa.String(length=255), nullable=True),
                    sa.Column('create_time', sa.BigInteger(), nullable=True),
                    sa.ForeignKeyConstraint(['project_id'], ['project.uuid'], onupdate='cascade'),
                    sa.PrimaryKeyConstraint('uuid'),
                    sqlite_autoincrement=True
                    )
    op.create_table('workflow',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('project_id', sa.BigInteger(), nullable=True),
                    sa.Column('properties', sa.String(length=1000), nullable=True),
                    sa.Column('create_time', sa.BigInteger(), nullable=True),
                    sa.Column('update_time', sa.BigInteger(), nullable=True),
                    sa.Column('is_deleted', sa.Boolean(), nullable=True),
                    sa.Column('context_extractor_in_bytes', sa.LargeBinary(), nullable=True),
                    sa.Column('graph', sa.Text(), nullable=True),
                    sa.Column('scheduling_rules', sa.Text(), nullable=True),
                    sa.Column('last_event_version', sa.BigInteger(), nullable=True),
                    sa.ForeignKeyConstraint(['project_id'], ['project.uuid'], onupdate='cascade'),
                    sa.PrimaryKeyConstraint('uuid'),
                    sa.UniqueConstraint('project_id', 'name'),
                    sqlite_autoincrement=True
                    )
    op.create_table('model_version_relation',
                    sa.Column('version', sa.String(length=255), nullable=False),
                    sa.Column('model_id', sa.BigInteger(), nullable=False),
                    sa.Column('project_snapshot_id', sa.BigInteger(), nullable=True),
                    sa.Column('is_deleted', sa.String(length=256), nullable=True),
                    sa.ForeignKeyConstraint(['model_id'], ['model_relation.uuid'], onupdate='cascade'),
                    sa.ForeignKeyConstraint(['project_snapshot_id'], ['project_snapshot.uuid'], onupdate='cascade'),
                    sa.PrimaryKeyConstraint('version', 'model_id')
                    )


def downgrade():
    op.drop_table('model_version_relation')
    op.drop_table('workflow')
    op.drop_table('project_snapshot')
    op.drop_table('model_version')
    op.drop_table('model_relation')
    op.drop_table('metric_summary')
    op.drop_table('workflow_execution_event_handler_state')
    op.drop_table('registered_model')
    op.drop_table('project')
    op.drop_table('metric_meta')
    op.drop_table('event')
    op.drop_table('dataset')
    op.drop_table('artifact')
