#!/usr/bin/env bash
##
## Copyright 2022 The AI Flow Authors
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
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
export AIRFLOW_HOME=${AIRFLOW_HOME:-~/airflow}
export AIRFLOW_SCHEDULER_PID_FILE="${AIRFLOW_HOME}/scheduler.pid"
export AIRFLOW_WEB_PID_FILE="${AIRFLOW_HOME}/web.pid"

kill_with_pid_file() {
  if [ ! -e "$2" ]; then
    echo "No $1 running"
  else
    echo "Stopping $1"
    for ((i=1;i<=3;i++))
    do
      kill $(cat "$2") >/dev/null 2>&1 && sleep 1
    done

    rm "$2" 2>/dev/null
    echo "$1 stopped"
  fi
}

set +e
kill_with_pid_file "airflow scheduler" "${AIRFLOW_SCHEDULER_PID_FILE}"
kill_with_pid_file "airflow web server" "${AIRFLOW_WEB_PID_FILE}"
