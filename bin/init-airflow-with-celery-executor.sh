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

usage="Usage: init-airflow-with-celery-executor.sh [airflow-mysql-conn] [notification_server_uri]"

if [ $# -ne 2 ]; then
  echo "${usage}"
  exit 1
fi

export AIRFLOW_HOME=${AIRFLOW_HOME:-~/airflow}
MYSQL_CONN=$1
NOTIFICATION_SERVER_URI=$2
BIN=$(dirname "${BASH_SOURCE-$0}")
BIN=$(cd "$BIN"; pwd)

if [[ ! -f "${AIRFLOW_HOME}/airflow.cfg" ]] ; then
  "${BIN}"/init-airflow-env.sh
fi

CURRENT_DIR=$(pwd)
cd "${AIRFLOW_HOME}"
mv airflow.cfg airflow.cfg.tmpl
awk "{gsub(\"executor = LocalExecutor\", \"executor = CeleryExecutor\"); \
    gsub(\"sql_alchemy_conn = sqlite:///${AIRFLOW_HOME}/airflow.db\", \"sql_alchemy_conn = ${MYSQL_CONN}\"); \
    gsub(\"notification_server_uri = 127.0.0.1:50052\", \"notification_server_uri = ${NOTIFICATION_SERVER_URI}\"); \
    print \$0}" airflow.cfg.tmpl > airflow.cfg
rm airflow.cfg.tmpl >/dev/null 2>&1 || true
cd "${CURRENT_DIR}"