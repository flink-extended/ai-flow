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

export AIFLOW_HOME=${AIFLOW_HOME:-~/aiflow}
export NOTIFICATION_HOME=${NOTIFICATION_HOME:-~/notification_service}

# start notification service
if [ -e "${NOTIFICATION_HOME}"/notification_server.pid ]; then
  echo "Notification server is running, stop it first."
  notification server stop
fi
notification config init
notification db init
notification server start -d
sleep 3
echo "Waiting for Notification Server started..."

# start airflow scheduler and web server
"${BIN}"/start-airflow.sh

# start AIFlow
if [ -e "${AIFLOW_HOME}"/aiflow_server.pid ] || [ -e "${AIFLOW_HOME}"/aiflow_web_server.pid ]; then
  echo "AIFlow is running, stopping first"
  aiflow server stop
  aiflow webserver stop
fi
aiflow config init
aiflow db init
aiflow server start -d
aiflow webserver start -d

echo "All services have been started!"
