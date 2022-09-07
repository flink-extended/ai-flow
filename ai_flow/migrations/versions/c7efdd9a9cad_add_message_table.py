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

"""add message table

Revision ID: c7efdd9a9cad
Revises: 7edd3c063e94
Create Date: 2022-06-05 15:37:44.650789

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7efdd9a9cad'
down_revision = '7edd3c063e94'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'message',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('type', sa.String(length=256), nullable=False),
        sa.Column('data', sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )


def downgrade():
    op.drop_table('message')
