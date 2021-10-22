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
export AIRFLOW_HOME=${AIRFLOW_HOME:-~/airflow}
[ -d "${AIRFLOW_HOME}" ] || mkdir "${AIRFLOW_HOME}"

export AIRFLOW_LOG_DIR=${AIRFLOW_HOME}/logs
[ -d "${AIRFLOW_LOG_DIR}" ] || mkdir "${AIRFLOW_LOG_DIR}"

export AIRFLOW_PID_DIR=${AIRFLOW_PID_DIR:-${AIRFLOW_HOME}}
[ -d "${AIRFLOW_PID_DIR}" ] || mkdir "${AIRFLOW_PID_DIR}"

export AIRFLOW_DAG_DIR=${AIRFLOW_DAG_DIR:-${AIRFLOW_HOME}/dags}
[ -d "${AIRFLOW_DAG_DIR}" ] || mkdir "${AIRFLOW_DAG_DIR}"

export NOTIFICATION_SERVER_URI=${NOTIFICATION_SERVER_URI:-127.0.0.1:50052}
