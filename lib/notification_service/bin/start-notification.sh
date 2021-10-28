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

BIN=$(dirname "${BASH_SOURCE-$0}")
BIN=$(cd "$BIN"; pwd)
. "${BIN}"/init-notification-env.sh

function start_server() {
  if [ -e "${NOTIFICATION_PID_FILE}" ]; then
    echo "Notification server is running, stopping first"
    "${BIN}"/stop-notification.sh
  fi

  echo "Starting notification server"
  LOG_FILE_NAME=notification_service-$(date "+%Y%m%d-%H%M%S").log
  start_notification_service.py --config-file="$CONFIG_FILE" > "${NOTIFICATION_LOG_DIR}"/"${LOG_FILE_NAME}" 2>&1 &
  echo $! > "${NOTIFICATION_PID_FILE}"

  echo "notification server started"
  echo "Notification server log: ${NOTIFICATION_LOG_DIR}/${LOG_FILE_NAME}"
  echo "Notification server pid: $(cat "${NOTIFICATION_PID_FILE}")"
}

usage="Usage: start-notification.sh"

if [ $# -eq 0 ]; then
  CONFIG_FILE=${NOTIFICATION_CONFIG_FILE}
else
  echo "$usage"
  exit 1
fi

start_server