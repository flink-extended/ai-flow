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

import logging
import os
import shutil

from ai_flow.metadata.base import Base
from ai_flow.common.util.db_util import db_migration
from ai_flow.common.configuration import config_constants

_logger = logging.getLogger(__name__)
db_uri = config_constants.METADATA_BACKEND_URI


def init(args):
    """Init the metadata database"""
    _logger.info('Initialize the database, db uri: {}'.format(db_uri))
    db_migration.init_db(url=db_uri)


def reset(args):
    """Reset the metadata database"""
    _logger.info('Reset the database, db uri: {}'.format(db_uri))
    if args.yes or input("This will drop existing tables if they exist. Proceed? (y/n)").upper() == "Y":
        db_migration.reset_db(url=db_uri, metadata=Base.metadata)
        if os.path.isdir(config_constants.LOCAL_REGISTRY_PATH):
            shutil.rmtree(config_constants.LOCAL_REGISTRY_PATH)
    else:
        _logger.info('Cancel reset the database, db uri: {}'.format(db_uri))


def upgrade(args):
    """Upgrade the metadata database"""
    _logger.info('Upgrade the database, db uri: {}'.format(db_uri))
    db_migration.upgrade(url=db_uri, version=args.version)


def downgrade(args):
    """Downgrade the metadata database"""
    _logger.info('Downgrade the database, db uri: {}'.format(db_uri))
    db_migration.downgrade(url=db_uri, version=args.version)
