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
export AIFLOW_HOME=${AIFLOW_HOME:-~/aiflow}
export AIFLOW_PID_DIR=${AIFLOW_PID_DIR:-${AIFLOW_HOME}}
export AIFLOW_LOG_DIR="${AIFLOW_HOME}/logs"

# create directory if not exist
[ -d "${AIFLOW_HOME}" ] || mkdir "${AIFLOW_HOME}"
[ -d "${AIFLOW_PID_DIR}" ] || mkdir "${AIFLOW_PID_DIR}"
[ -d "${AIFLOW_LOG_DIR}" ] || mkdir "${AIFLOW_LOG_DIR}"
