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
export AIRFLOW_HOME=${AIRFLOW_HOME:-~/airflow}
[ -d "${AIRFLOW_HOME}" ] || mkdir "${AIRFLOW_HOME}"

export AIRFLOW_LOG_DIR=${AIRFLOW_HOME}/logs
[ -d "${AIRFLOW_LOG_DIR}" ] || mkdir "${AIRFLOW_LOG_DIR}"

export AIRFLOW_SCHEDULER_PID_FILE="${AIRFLOW_HOME}/scheduler.pid"
export AIRFLOW_WEB_PID_FILE="${AIRFLOW_HOME}/web.pid"

export AIRFLOW_DAG_DIR="${AIRFLOW_HOME}/dags"
[ -d "${AIRFLOW_DAG_DIR}" ] || mkdir "${AIRFLOW_DAG_DIR}"

init_airflow_config() {
  if [[ ! -f "${AIRFLOW_HOME}/airflow.cfg" ]] ; then
    echo "${AIRFLOW_HOME}/airflow.cfg does not exist creating one."
    CURRENT_DIR=$(pwd)
    cd "${AIRFLOW_HOME}" || exit

    # create the configuration file
    airflow config list >/dev/null 2>&1 || true
    cd "${CURRENT_DIR}" || exit
  else
    echo "${AIRFLOW_HOME}/airflow.cfg already exist. Using the existing airflow.cfg"
  fi
}
init_airflow_db(){
  # init database
  airflow db init
  # create a default Admin user for airflow
  echo "Creating admin airflow user"
  airflow users create \
      --username admin \
      --password admin \
      --firstname admin \
      --lastname admin \
      --role Admin \
      --email admin@example.org
}

init_airflow_config

init_airflow_db