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
import subprocess
import time
from typing import List, Optional, Dict, Any, Union, Iterator

from ai_flow.common.env import expand_env_var
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.context import Context
from ai_flow.model.operator import AIFlowOperator


class SparkSubmitOperator(AIFlowOperator):
    """
    SparkSubmitOperator is used to submit spark job with spark-submit command line.

    :param name: The name of the operator.
    :param application: The application file to be submitted, like app jar, python file or R file.
    :param application_args: Args of the application.
    :param executable_path: The path of spark-submit command.
    :param master: spark://host:port, mesos://host:port, yarn, k8s://https://host:port, or local.
    :param deploy_mode: Launch the program in client(by default) mode or cluster mode.
    :param application_name: The name of spark application.
    :param submit_options: The options that passes to command-line, e.g. --conf, --class and --files
    :param k8s_namespace: The namespace of k8s, when submit application to k8s, it should be passed.
    :param env_vars: Environment variables for spark-submit. It supports yarn and k8s mode too.
    :param status_poll_interval: Seconds to wait between polls of driver status in cluster mode (Default: 1)
    """

    def __init__(self,
                 name: str,
                 application: str,
                 application_args: Optional[List[Any]] = None,
                 executable_path: Optional[str] = None,
                 master: str = 'yarn',
                 deploy_mode: str = 'client',
                 application_name: str = None,
                 submit_options: Optional[str] = None,
                 k8s_namespace: Optional[str] = None,
                 env_vars: Optional[Dict[str, Any]] = None,
                 status_poll_interval: int = 1,
                 **kwargs):
        super().__init__(name, **kwargs)
        self._application = application
        self._application_name = application_name or f'spark_submit_task_{name}'
        self._executable_path = executable_path
        self._master = master
        self._deploy_mode = deploy_mode
        self._env_vars = env_vars
        self._submit_options = submit_options
        self._application_args = application_args
        self._status_poll_interval = status_poll_interval

        self._is_yarn = self._master is not None and 'yarn' in self._master
        self._is_kubernetes = self._master is not None and 'k8s' in self._master
        self._kubernetes_namespace = k8s_namespace

        self._env: Optional[Dict[str, Any]] = None
        self.spark_submit_cmd = None
        self._process = None

        self._yarn_application_id = None
        self._kubernetes_driver_pod = None
        self._driver_id = None
        self._driver_status = None
        self._spark_exit_code = None
        self._should_track_driver_status = self._resolve_should_track_driver_status()

    def start(self, context: Context):
        self.spark_submit_cmd = self._build_spark_submit_command()
        kwargs = {}

        if self._env:
            env = os.environ.copy()
            env.update(self._env)
            kwargs["env"] = env

        self._process = subprocess.Popen(
            self.spark_submit_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=-1,
            universal_newlines=True,
            **kwargs,
        )

    def await_termination(self, context: Context, timeout: Optional[int] = None):
        self._process_spark_submit_log(iter(self._process.stdout))
        return_code = self._process.wait()

        if return_code or (self._is_kubernetes and self._spark_exit_code != 0):
            if self._is_kubernetes:
                raise AIFlowException(
                    "Cannot execute: {}. Error code is: {}. Kubernetes spark exit code is: {}".format(
                        self._mask_cmd(self.spark_submit_cmd), return_code, self._spark_exit_code
                    )
                )
            else:
                raise AIFlowException(
                    "Cannot execute: {}. Error code is: {}.".format(
                        self._mask_cmd(self.spark_submit_cmd), return_code
                    )
                )
        if self._should_track_driver_status:
            if self._driver_id is None:
                raise AIFlowException(
                    "No driver id is known: something went wrong when executing the spark submit command"
                )
            self._driver_status = "SUBMITTED"
            self._start_driver_status_tracking()
            if self._driver_status != "FINISHED":
                raise AIFlowException(
                    "ERROR : Driver {} badly exited with status {}".format(
                        self._driver_id, self._driver_status
                    )
                )

    def stop(self, context: Context):
        if self._should_track_driver_status:
            if self._driver_id:
                kill_cmd = self._build_spark_driver_kill_command()
                driver_kill = subprocess.Popen(kill_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.log.info(
                    "Spark driver %s killed with return code: %s", self._driver_id, driver_kill.wait()
                )
        if self._process and self._process.poll() is None:
            self._process.kill()

            self.log.info(f"application id is {self._yarn_application_id}")
            if self._yarn_application_id:
                kill_cmd = f"yarn application -kill {self._yarn_application_id}".split()
                yarn_kill = subprocess.Popen(
                    kill_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                yarn_kill.wait()

            if self._kubernetes_driver_pod:
                self.log.info('Killing pod %s on Kubernetes', self._kubernetes_driver_pod)

                try:
                    import kubernetes
                    from kubernetes import client
                    from kubernetes import config
                    from kubernetes.client.rest import ApiException

                    kube_client = client.CoreV1Api().get_kube_client()
                    api_response = kube_client.delete_namespaced_pod(
                        self._kubernetes_driver_pod,
                        self._kubernetes_namespace,
                        body=kubernetes.client.V1DeleteOptions(),
                        pretty=True,
                    )
                    self.log.info("Spark on K8s killed with response: %s", api_response)
                except ApiException as e:
                    self.log.error("Exception when attempting to kill Spark on K8s:")
                    self.log.exception(e)

    def _resolve_should_track_driver_status(self) -> bool:
        return 'spark://' in self._master and self.deploy_mode == 'cluster'

    def _get_executable_path(self):
        if self._executable_path:
            spark_submit = self._executable_path
        else:
            spark_submit = expand_env_var('${SPARK_HOME}/bin/spark-submit')
        if not os.path.exists(spark_submit):
            raise AIFlowException(f'Cannot find spark-submit at {spark_submit}')
        return spark_submit

    def _build_spark_submit_command(self) -> List[str]:
        spark_submit_command = [self._get_executable_path()]
        if self._master:
            spark_submit_command += ["--master", self._master]
        if self._deploy_mode:
            spark_submit_command += ["--deploy-mode", self._deploy_mode]
        if self._application_name:
            spark_submit_command += ["--name", self._application_name]
        if self._env_vars and (self._is_kubernetes or self._is_yarn):
            if self._is_yarn:
                tmpl = "spark.yarn.appMasterEnv.{}={}"
                self._env = self._env_vars
            else:
                tmpl = "spark.kubernetes.driverEnv.{}={}"
            for key in self._env_vars:
                spark_submit_command += ["--conf", tmpl.format(key, str(self._env_vars[key]))]
        elif self._env_vars and self._deploy_mode == "client":
            self._env = self._env_vars  # Do it on Popen of the process
        elif self._env_vars and self._deploy_mode == "cluster":
            raise AIFlowException("SparkSubmitOperator env_vars is not supported in standalone-cluster mode.")
        if self._is_kubernetes:
            if not self._kubernetes_namespace:
                raise AIFlowException("Param k8s_namespace must be set when submit to k8s.")
            spark_submit_command += [
                "--conf", f"spark.kubernetes.namespace={self._kubernetes_namespace}",
            ]
        if self._submit_options:
            spark_submit_command += self._submit_options.split()

        spark_submit_command += [self._application]

        if self._application_args:
            spark_submit_command += self._application_args

        self.log.info("Spark-Submit cmd: %s", self._mask_cmd(spark_submit_command))

        return spark_submit_command

    @staticmethod
    def _mask_cmd(cmd: Union[str, List[str]]) -> str:
        cmd_masked = re.sub(
            r"("
            r"\S*?"  # Match all non-whitespace characters before...
            r"(?:secret|password)"  # ...literally a "secret" or "password"
            # word (not capturing them).
            r"\S*?"  # All non-whitespace characters before either...
            r"(?:=|\s+)"  # ...an equal sign or whitespace characters
            # (not capturing them).
            r"(['\"]?)"  # An optional single or double quote.
            r")"  # This is the end of the first capturing group.
            r"(?:(?!\2\s).)*"  # All characters between optional quotes
            # (matched above); if the value is quoted,
            # it may contain whitespace.
            r"(\2)",  # Optional matching quote.
            r'\1******\3',
            ' '.join(cmd),
            flags=re.I,
        )

        return cmd_masked

    def _process_spark_submit_log(self, itr: Iterator[Any]) -> None:
        for line in itr:
            line = line.strip()
            if self._is_yarn and self._deploy_mode == 'cluster':
                match = re.search('(application[0-9_]+)', line)
                if match:
                    self._yarn_application_id = match.groups()[0]
                    self.log.info("Identified spark driver id: %s", self._yarn_application_id)
            elif self._is_kubernetes:
                match = re.search(r'\s*pod name: ((.+?)-([a-z0-9]+)-driver)', line)
                if match:
                    self._kubernetes_driver_pod = match.groups()[0]
                    self.log.info("Identified spark driver pod: %s", self._kubernetes_driver_pod)

                match_exit_code = re.search(r'\s*[eE]xit code: (\d+)', line)
                if match_exit_code:
                    self._spark_exit_code = int(match_exit_code.groups()[0])
            elif self._should_track_driver_status and not self._driver_id:
                match_driver_id = re.search(r'(driver-[0-9\-]+)', line)
                if match_driver_id:
                    self._driver_id = match_driver_id.groups()[0]
                    self.log.info("identified spark driver id: %s", self._driver_id)
            self.log.info(line)

    def _start_driver_status_tracking(self) -> None:
        missed_job_status_reports = 0
        max_missed_job_status_reports = 10

        while self._driver_status not in ["FINISHED", "UNKNOWN", "KILLED", "FAILED", "ERROR"]:
            time.sleep(self._status_poll_interval)
            poll_drive_status_cmd = self._build_track_driver_status_command()
            status_process: Any = subprocess.Popen(
                poll_drive_status_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=-1,
                universal_newlines=True,
            )
            self._process_spark_status_log(iter(status_process.stdout))
            ret_code = status_process.wait()

            if ret_code:
                if missed_job_status_reports < max_missed_job_status_reports:
                    missed_job_status_reports += 1
                else:
                    raise AIFlowException(
                        "Failed to poll for the driver status {} times: return code = {}".format(
                            max_missed_job_status_reports, ret_code
                        )
                    )

    def _build_track_driver_status_command(self) -> List[str]:
        curl_max_wait_time = 30
        if self._master.endswith(':6066'):
            spark_host = self._master.replace("spark://", "http://")
            status_command = [
                "/usr/bin/curl",
                "--max-time",
                str(curl_max_wait_time),
                f"{spark_host}/v1/submissions/status/{self._driver_id}",
            ]
            if not self._driver_id:
                raise AIFlowException(
                    "Invalid status: attempted to poll driver "
                    + "status but no driver id is known. Giving up."
                )
        else:
            status_command = self.executable_path + ["--master", self._master]
            if self._driver_id:
                status_command += ["--status", self._driver_id]
            else:
                raise AIFlowException(
                    "Invalid status: attempted to poll driver "
                    + "status but no driver id is known. Giving up."
                )
        self.log.debug("Poll driver status cmd: %s", status_command)
        return status_command

    def _process_spark_status_log(self, itr: Iterator[Any]) -> None:
        driver_found = False
        for line in itr:
            line = line.strip()
            if "driverState" in line:
                self._driver_status = line.split(' : ')[1].replace(',', '').replace('\"', '').strip()
                driver_found = True
            self.log.debug("spark driver status log: %s", line)
        if not driver_found:
            self._driver_status = "UNKNOWN"

    def _build_spark_driver_kill_command(self) -> List[str]:
        spark_kill_command = [self._get_executable_path()]
        spark_kill_command += ["--master", self._master]
        if self._driver_id:
            spark_kill_command += ["--kill", self._driver_id]
        return spark_kill_command
