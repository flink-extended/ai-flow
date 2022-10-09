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
import re
import shutil
import subprocess
from typing import List, Optional, Dict, Any, Iterator

from ai_flow.common.util.string_utils import mask_cmd

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
    :param master: spark://host:port, yarn, mesos://host:port, k8s://https://host:port, or local.
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

        self._validate_parameters()

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
                        mask_cmd(self.spark_submit_cmd), return_code, self._spark_exit_code
                    )
                )
            else:
                raise AIFlowException(
                    "Cannot execute: {}. Error code is: {}.".format(
                        mask_cmd(self.spark_submit_cmd), return_code
                    )
                )

    def stop(self, context: Context):
        if self._process and self._process.poll() is None:
            self._process.kill()

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

    def _validate_parameters(self):
        is_standalone = 'spark://' in self._master
        is_mesos = 'mesos' in self._master
        if is_standalone and self._deploy_mode == 'cluster':
            raise AIFlowException('Only client mode is supported with standalone cluster.')
        if is_mesos and self._deploy_mode == 'cluster':
            raise AIFlowException('Only client mode is supported with mesos cluster.')
        if self._is_kubernetes and not self._kubernetes_namespace:
            raise AIFlowException("Param k8s_namespace must be set when submit to k8s.")

    def _get_executable_path(self):
        if self._executable_path:
            spark_submit = self._executable_path
        elif shutil.which('spark-submit') is not None:
            spark_submit = shutil.which('spark-submit')
            self.log.info(f"Using {spark_submit} in PATH")
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
            self._env = self._env_vars
        if self._is_kubernetes:
            spark_submit_command += [
                "--conf", f"spark.kubernetes.namespace={self._kubernetes_namespace}",
            ]
        if self._submit_options:
            spark_submit_command += self._submit_options.split()

        spark_submit_command += [self._application]

        if self._application_args:
            spark_submit_command += self._application_args

        self.log.info("Spark-Submit cmd: %s", mask_cmd(spark_submit_command))

        return spark_submit_command

    def _process_spark_submit_log(self, itr: Iterator[Any]) -> None:
        for line in itr:
            line = line.strip()
            if self._is_yarn and self._deploy_mode == 'cluster':
                match = re.search('(application[0-9_]+)', line)
                if match:
                    self._yarn_application_id = match.groups()[0]
                    self.log.info("Identified yarn application id: %s", self._yarn_application_id)
            elif self._is_kubernetes:
                match = re.search(r'\s*pod name: ((.+?)-([a-z0-9]+)-driver)', line)
                if match:
                    self._kubernetes_driver_pod = match.groups()[0]
                    self.log.info("Identified spark driver pod: %s", self._kubernetes_driver_pod)

                match_exit_code = re.search(r'\s*[eE]xit code: (\d+)', line)
                if match_exit_code:
                    self._spark_exit_code = int(match_exit_code.groups()[0])
            self.log.info(line)
