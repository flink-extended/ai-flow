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

"""model_version_add_createtime

Revision ID: 3ba5526346e3
Revises: 0e8fefcce376
Create Date: 2022-02-15 17:17:04.220562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ba5526346e3'
down_revision = '0e8fefcce376'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('model_version') as batch_op:
        batch_op.alter_column('model_version', type_=sa.Integer())
        batch_op.add_column(sa.Column('create_time', sa.BigInteger(), nullable=True))
    with op.batch_alter_table('model_version_relation') as batch_op:
        batch_op.alter_column('version', type_=sa.Integer())
    with op.batch_alter_table('metric_summary') as batch_op:
        batch_op.alter_column('model_version', type_=sa.Integer())


def downgrade():
    with op.batch_alter_table('model_version') as batch_op:
        batch_op.alter_column('model_version', type_=sa.String(10))
        batch_op.drop_column('create_time')
    with op.batch_alter_table('model_version_relation') as batch_op:
        batch_op.alter_column('version', type_=sa.String(10))
    with op.batch_alter_table('metric_summary') as batch_op:
        batch_op.alter_column('model_version', type_=sa.String(10))
