#
# Copyright 2022 The AI Flow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import os
import subprocess
from typing import Optional

from ai_flow.common.env import expand_env_var
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.context import Context
from ai_flow.model.operator import AIFlowOperator


class SparkSqlOperator(AIFlowOperator):
    """
    SparkSqlOperator only supports client mode for now.
    """

    def __init__(self,
                 name: str,
                 sql: str,
                 master: str = 'yarn',
                 application_name: str = None,
                 executable_path: Optional[str] = None,
                 **kwargs):
        super().__init__(name, **kwargs)
        self._application_name = application_name or f'spark_sql_task_{name}'
        self._master = master
        self._executable_path = executable_path
        self._sql = sql
        self._spark_sql_cmd = None
        self._process = None

    def start(self, context: Context):
        self._spark_sql_cmd = self._build_spark_sql_command()
        kwargs = {}

        self._process = subprocess.Popen(
            self._spark_sql_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=-1,
            universal_newlines=True,
            **kwargs,
        )

    def await_termination(self, context: Context, timeout: Optional[int] = None):
        for line in iter(self._process.stdout):  # type: ignore
            self.log.info(line)

        ret_code = self._process.wait()
        if ret_code:
            raise AIFlowException(
                "Cannot execute '{}' on {}. Process exit code: {}.".format(
                    self._sql, self._master, ret_code
                )
            )

    def stop(self, context: Context):
        if self._process and self._process.poll() is None:
            self.log.info("Killing the Spark-Sql job")
            self._process.kill()

    def _get_executable_path(self):
        if self._executable_path:
            spark_sql = self._executable_path
        else:
            spark_sql = expand_env_var('${SPARK_HOME}/bin/spark-sql')
        if not os.path.exists(spark_sql):
            raise AIFlowException(f'Cannot find spark-sql at {spark_sql}')
        return spark_sql

    def _build_spark_sql_command(self):
        spark_sql_cmd = [self._get_executable_path()]
        if self._application_name:
            spark_sql_cmd += ["--name", self._application_name]
        if self._sql:
            sql = self._sql.strip()
            if sql.endswith(".sql") or sql.endswith(".hql"):
                spark_sql_cmd += ["-f", sql]
            else:
                spark_sql_cmd += ["-e", sql]
        self.log.debug("Spark-Sql cmd: %s", spark_sql_cmd)

        return spark_sql_cmd


