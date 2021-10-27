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
export NOTIFICATION_PID_DIR=${NOTIFICATION_PID_DIR:-${NOTIFICATION_HOME}}
export NOTIFICATION_PID_FILE="${NOTIFICATION_PID_DIR}/notification_server.pid"
export NOTIFICATION_LOG_DIR="${NOTIFICATION_HOME}/logs"
export NOTIFICATION_SERVER_PORT=${NOTIFICATION_SERVER_PORT:-50052}
export NOTIFICATION_CONFIG_FILE="${NOTIFICATION_HOME}/notification_server.yaml"
export NOTIFICATION_DB_CONN="${NOTIFICATION_DB_CONN:-sqlite:///${NOTIFICATION_HOME}/ns.db}"
export NOTIFICATION_ADVERTISED_URI="${NOTIFICATION_ADVERTISED_URI:-127.0.0.1:${NOTIFICATION_SERVER_PORT}}"

function create_notification_dirs() {
  [ -d "${NOTIFICATION_HOME}" ] || mkdir "${NOTIFICATION_HOME}"
  [ -d "${NOTIFICATION_PID_DIR}" ] || mkdir "${NOTIFICATION_PID_DIR}"
  [ -d "${NOTIFICATION_LOG_DIR}" ] || mkdir "${NOTIFICATION_LOG_DIR}"
}
create_notification_dirs
