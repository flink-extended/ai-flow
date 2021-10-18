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

"""add_workflow_snapshot

Revision ID: 0e8fefcce376
Revises: de045f309236
Create Date: 2021-11-24 10:08:58.313703

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e8fefcce376'
down_revision = 'de045f309236'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('workflow_snapshot',
                    sa.Column('uuid', sa.BigInteger(), autoincrement=True, nullable=False),
                    sa.Column('workflow_id', sa.BigInteger(), nullable=False),
                    sa.Column('uri', sa.String(length=1000), nullable=True),
                    sa.Column('signature', sa.String(length=1000), nullable=True),
                    sa.Column('create_time', sa.BigInteger(), nullable=True),
                    sa.PrimaryKeyConstraint('uuid'),
                    sa.ForeignKeyConstraint(['workflow_id'], ['workflow.uuid'], onupdate='cascade'),
                    )


def downgrade():
    op.drop_table('workflow_snapshot')
