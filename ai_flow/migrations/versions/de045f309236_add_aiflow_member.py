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

"""add_aiflow_member

Revision ID: de045f309236
Revises: de1c96ef582a
Create Date: 2021-10-13 16:48:26.412700

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'de045f309236'
down_revision = 'de1c96ef582a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('aiflow_member',
                    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
                    sa.Column('version', sa.BigInteger(), nullable=False),
                    sa.Column('server_uri', sa.String(length=767), nullable=False),
                    sa.Column('update_time', sa.BigInteger(), nullable=False),
                    sa.Column('uuid', sa.String(length=128), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('server_uri'),
                    sa.UniqueConstraint('uuid')
                    )


def downgrade():
    op.drop_table('aiflow_member')
