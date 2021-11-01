#!/usr/bin/env bash
##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
set -e
export NOTIFICATION_HOME=${NOTIFICATION_HOME:-~/notification_service}
export NOTIFICATION_PID_FILE="${NOTIFICATION_HOME}/notification_server.pid"
export NOTIFICATION_LOG_DIR="${NOTIFICATION_HOME}/logs"
export NOTIFICATION_CONFIG_FILE="${NOTIFICATION_HOME}/notification_server.yaml"

function create_notification_dirs() {
  [ -d "${NOTIFICATION_HOME}" ] || mkdir "${NOTIFICATION_HOME}"
  [ -d "${NOTIFICATION_LOG_DIR}" ] || mkdir "${NOTIFICATION_LOG_DIR}"
}
create_notification_dirs

if [ ! -e ${NOTIFICATION_CONFIG_FILE} ]; then
  echo "Notification server config doesn't exist generating at ${NOTIFICATION_CONFIG_FILE}"
  BIN=$(dirname "${BASH_SOURCE-$0}")
  BIN=$(cd "$BIN"; pwd)
  "$BIN"/start_notification_server.py --generate-config-only > /dev/null 2>&1
else
  echo "Notification server config already exist at ${NOTIFICATION_CONFIG_FILE}"
fi