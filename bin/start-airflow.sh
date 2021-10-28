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
. "${BIN}"/init-airflow-env.sh

usage="Usage: start-airflow.sh"
if [ $# -ne 0 ]; then
  echo "$usage"
  exit 1
fi

wait_for_airflow_web_server() {
  for i in {0..60}; do
    if [ -e "${AIRFLOW_LOG_DIR}/$1" ] && (grep -q 'Listening at:' "${AIRFLOW_LOG_DIR}"/"$1" || curl -s localhost:8080 > /dev/null) ; then
      return 0
    fi
    sleep 1
  done
  echo "Timeout waiting for airflow web server to run. Please check the log at ${AIRFLOW_LOG_DIR}/$1"
  return 1
}

# Stop the running scheduler and web server if already running
if [ -e "${AIRFLOW_SCHEDULER_PID_FILE}" ] || [ -e "${AIRFLOW_WEB_PID_FILE}" ]; then
  echo "Airflow is running, stop it first."
  "${BIN}"/stop-airflow.sh
fi

echo "Starting Airflow Scheduler"
SCHEDULER_LOG_FILE_NAME=scheduler-$(date "+%Y%m%d-%H%M%S").log
airflow event_scheduler > "${AIRFLOW_LOG_DIR}"/"${SCHEDULER_LOG_FILE_NAME}" 2>&1 &
echo $! > "${AIRFLOW_SCHEDULER_PID_FILE}"
echo "Airflow Scheduler started"

echo "Starting Airflow Web Server"
WEB_SERVER_LOG_FILE_NAME=web-$(date "+%Y%m%d-%H%M%S").log
airflow webserver -p 8080 > "${AIRFLOW_LOG_DIR}"/"${WEB_SERVER_LOG_FILE_NAME}" 2>&1 &
echo $! > "${AIRFLOW_WEB_PID_FILE}"
wait_for_airflow_web_server "${WEB_SERVER_LOG_FILE_NAME}"
echo "Airflow Web Server started"

echo "Scheduler log: ${AIRFLOW_LOG_DIR}/${SCHEDULER_LOG_FILE_NAME}"
echo "Scheduler pid: $(cat "${AIRFLOW_SCHEDULER_PID_FILE}")"
echo "Web Server log: ${AIRFLOW_LOG_DIR}/${WEB_SERVER_LOG_FILE_NAME}"
echo "Web Server pid: $(cat "${AIRFLOW_WEB_PID_FILE}")"
echo "Airflow deploy path: ${AIRFLOW_DAG_DIR}"

