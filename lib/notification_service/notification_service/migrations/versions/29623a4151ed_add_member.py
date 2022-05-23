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

"""add_member

Revision ID: 29623a4151ed
Revises: 87cb292bcc31
Create Date: 2021-10-15 12:06:45.611155

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '29623a4151ed'
down_revision = '87cb292bcc31'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('member_model',
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
    op.drop_table('member_model')