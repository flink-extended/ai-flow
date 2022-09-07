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

"""add_tables

Revision ID: 87cb292bcc31
Revises: 
Create Date: 2021-10-15 12:04:11.696836

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '87cb292bcc31'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('event_model',
                    sa.Column('offset', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
                    sa.Column('key', sa.String(length=1024), nullable=False),
                    sa.Column('value', sa.Text(), nullable=True),
                    sa.Column('context', sa.Text(), nullable=True),
                    sa.Column('namespace', sa.String(length=1024), nullable=True),
                    sa.Column('sender', sa.String(length=1024), nullable=True),
                    sa.Column('create_time', sa.BigInteger(), nullable=False),
                    sa.Column('uuid', sa.String(length=40), nullable=False),
                    sa.PrimaryKeyConstraint('offset'),
                    sa.UniqueConstraint('uuid')
                    )
    op.create_table('notification_client',
                    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True,
                              nullable=False),
                    sa.Column('namespace', sa.String(length=1024), nullable=True),
                    sa.Column('sender', sa.String(length=1024), nullable=True),
                    sa.Column('create_time', sa.BigInteger(), nullable=True),
                    sa.Column('is_deleted', sa.Boolean(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('notification_client')
    op.drop_table('event_model')
