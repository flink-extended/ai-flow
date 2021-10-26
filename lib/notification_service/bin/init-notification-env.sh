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
export NOTIFICATION_LOG_DIR="${NOTIFICATION_HOME}/logs"
export NOTIFICATION_SERVICE_PORT=${NOTIFICATION_SERVICE_PORT:-50052}

[ -d "${NOTIFICATION_HOME}" ] || mkdir "${NOTIFICATION_HOME}"
[ -d "${NOTIFICATION_PID_DIR}" ] || mkdir "${NOTIFICATION_PID_DIR}"
[ -d "${NOTIFICATION_LOG_DIR}" ] || mkdir "${NOTIFICATION_LOG_DIR}"

DEFAULT_NOTIFICATION_SERVER_URI="localhost:${NOTIFICATION_SERVICE_PORT}"
function get_ip_addr() {
  SYSTEM=$(uname -s)
  if [[ ${SYSTEM} == "Darwin" ]]; then
    DEFAULT_NOTIFICATION_SERVER_URI="$(ifconfig | grep "inet " | grep -Fv 127.0.0.1 | awk '{print $2}'):${NOTIFICATION_SERVICE_PORT}"
  elif [[ ${SYSTEM} == "Linux" ]]; then
    DEFAULT_NOTIFICATION_SERVER_URI="$(hostname -I | xargs):${NOTIFICATION_SERVICE_PORT}"
  else
    echo "Please init AIFlow on Linux or macOS."
    exit 1
  fi
}
get_ip_addr
export NOTIFICATION_SERVER_URI=${NOTIFICATION_SERVER_URI:-${DEFAULT_NOTIFICATION_SERVER_URI}}