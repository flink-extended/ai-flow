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

usage="Usage: start-all-aiflow-services.sh [notification-service-mysql-conn] [airflow-mysql-conn] [aiflow-mysql-conn]"
if [ $# -ne 3 ]; then
  echo "$usage"
  exit 1
fi
NOTIFICATION_SERVICE_DB_CONN=$1
AIRFLOW_DB_CONN=$2
export AIFLOW_DB_CONN=$3
export AIFLOW_DB_TYPE="MYSQL"

# start notification service
source "${BIN}"/init-notification-env.sh
"${BIN}"/start-notification.sh "${NOTIFICATION_SERVICE_DB_CONN}"
echo "notification service address: ${NOTIFICATION_SERVER_URI}"
sleep 3

# start airflow scheduler and web server
source "${BIN}"/init-airflow-env.sh
"${BIN}"/start-airflow.sh "${AIRFLOW_DB_CONN}" "${NOTIFICATION_SERVICE_DB_CONN}"
echo "airflow dag dir: ${AIRFLOW_DAG_DIR}"

# start AIFlow
source "${BIN}"/init-aiflow-env.sh
"${BIN}"/start-aiflow.sh "${AIFLOW_DB_CONN}"

echo "Visit http://127.0.0.1:8080/ to access the airflow web server."
