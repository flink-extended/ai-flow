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

AIFLOW_HOME=${AIFLOW_HOME:-~/aiflow}
AIFLOW_PID_DIR=${AIFLOW_PID_DIR:-${AIFLOW_HOME}}

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
kill_with_pid_file "AIFlow Server" "${AIFLOW_PID_DIR}"/aiflow_server.pid
kill_with_pid_file "AIFlow Web Server" "${AIFLOW_PID_DIR}"/aiflow_web_server.pid
