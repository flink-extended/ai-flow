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

"""add_timer_table

Revision ID: 7edd3c063e94
Revises: 04d531f52690
Create Date: 2022-05-17 15:45:20.165719

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7edd3c063e94'
down_revision = '04d531f52690'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'timer',
        sa.Column('id', sa.String(length=256), nullable=False),
        sa.Column('next_run_time', sa.Float(25), nullable=True),
        sa.Column('job_state', sa.LargeBinary, nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('timer')
