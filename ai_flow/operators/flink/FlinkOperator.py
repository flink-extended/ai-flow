#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
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
import re
import shutil
import subprocess
from typing import List, Optional, Any, Iterator

from ai_flow.common.env import expand_env_var
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.string_utils import mask_cmd
from ai_flow.model.context import Context
from ai_flow.model.operator import AIFlowOperator


class FlinkOperator(AIFlowOperator):
    """

    :param name: The name of the operator.
    """

    def __init__(self,
                 name: str,
                 application: str,
                 application_args: Optional[List[Any]] = None,
                 executable_path: Optional[str] = None,
                 application_mode: bool = False,
                 target: Optional[str] = None,
                 stop_with_savepoint: bool = True,
                 command_options: Optional[str] = None,
                 **kwargs):
        super().__init__(name, **kwargs)
        self._application = application
        self._application_args = application_args
        self._executable_path = executable_path
        self._application_mode = application_mode
        self._target = target
        self._stop_with_savepoint = stop_with_savepoint
        self._command_options = command_options

        self._flink_run_cmd = None
        self._process = None
        self._flink_job_id = None
        self._yarn_application_id = None

        self._is_yarn_application_mode = False
        self._is_kubernetes_application_mode = False
        self._is_yarn_per_job = False
        self._is_yarn_session = False
        self._is_remote = False
        self._is_local = False
        self._is_kubernetes_session = False

        self._validate_parameters()

    def start(self, context: Context):
        self._flink_run_cmd = self._build_flink_command()
        self._process = subprocess.Popen(
            self._flink_run_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=-1,
            universal_newlines=True,
        )

    def await_termination(self, context: Context, timeout: Optional[int] = None):
        self._process_flink_run_log(iter(self._process.stdout))
        return_code = self._process.wait()

        if return_code:
            raise AIFlowException(
                "Cannot execute: {}. Error code is: {}.".format(
                    mask_cmd(self._flink_run_cmd), return_code
                )
            )

    def stop(self, context: Context):
        if self._process and self._process.poll() is None:
            self._process.kill()

        if self._is_yarn_per_job or self._is_yarn_session:
            if not self._flink_job_id:
                raise AIFlowException("Flink job id not found.")
            if not self._yarn_application_id:
                raise AIFlowException("Yarn application id not found.")
            if self._stop_with_savepoint:
                kill_cmd = f"flink stop -yid {self._yarn_application_id} {self._flink_job_id}".split()
            else:
                kill_cmd = f"flink cancel -yid {self.__yarn_application_id} {self._flink_job_id}".split()



        kill_process = subprocess.Popen(
            kill_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        kill_process.wait()

    def _get_executable_path(self):
        if self._executable_path:
            executable = self._executable_path
        elif shutil.which('flink') is not None:
            executable = shutil.which('flink')
            self.log.info(f"Using {executable} in PATH")
        else:
            executable = expand_env_var('${FLINK_HOME}/bin/flink')
            if not os.path.exists(executable):
                raise AIFlowException(f'Cannot find flink command at {executable}')
        return executable

    def _build_flink_command(self):
        command = [self._get_executable_path()]
        if self._application_mode:
            command += ["run-application"]
        else:
            command += ["run"]
        if self._target:
            command += ["--target", self._target]
        if self._command_options:
            command += self._command_options.split()
        command += [self._application]

        if self._application_args:
            command += self._application_args

        self.log.info("flink run cmd: %s", mask_cmd(command))
        return command

    def _validate_parameters(self):
        if self._application_mode:
            if self._target == "yarn-application":
                self._is_yarn_application_mode = True
            elif self._target == "kubernetes-application":
                self._is_kubernetes_application_mode = True
            else:
                raise AIFlowException(
                    f'Invalid --target option: {self._target} set to `flink run-application`'
                )
        else:
            if self._target is None:
                pass
            elif self._target == 'yarn-per-job':
                self._is_yarn_per_job = True
            elif self._target == 'yarn-session':
                self._is_yarn_session = True
            elif self._target == 'remote':
                self._is_remote = True
            elif self._target == 'local':
                self._is_local = True
            elif self._target == 'kubernetes-session':
                self._is_kubernetes_session = True
            else:
                raise AIFlowException(
                    f'Invalid --target option: {self._target} set to `flink run`'
                )

    def _process_flink_run_log(self, itr: Iterator[Any]) -> None:
        for line in itr:
            line = line.strip()
            if not self._flink_job_id:
                match_job_id = re.search(r'^Job has been submitted with JobID ([a-z0-9]+)', line)
                if match_job_id:
                    self._flink_job_id = match_job_id.groups()[0]
                    self.log.info('Identified flink job id {}'.format(self._flink_job_id))
            if not self._yarn_application_id:
                match_yarn_app_id = re.search('(application[0-9_]+)', line)
                if match_yarn_app_id:
                    self._yarn_application_id = match_yarn_app_id.groups()[0]
                    self.log.info("Identified yarn application id: %s", self._yarn_application_id)
            self.log.info(line)

