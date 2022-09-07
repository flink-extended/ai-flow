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
import time
from typing import List, Optional, Any, Iterator

from ai_flow.common.env import expand_env_var
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.string_utils import mask_cmd
from ai_flow.model.context import Context
from ai_flow.model.operator import AIFlowOperator


class FlinkOperator(AIFlowOperator):
    """
    FlinkOperator is used to submit Flink job with flink command line.

    :param name: The name of the operator.
    :param application: The application file to be submitted, like app jar, python file.
    :param target: The deployment target for the given application,
                   which is equivalent to the "execution.target" config option.
    :param application_args: Args of the application.
    :param executable_path: The path of flink command.
    :param application_mode: Whether runs an application in Application Mode.
    :param stop_with_savepoint: Whether stops the flink job with a savepoint.
    :param kubernetes_cluster_id: Cluster id when submit flink job to kubernetes.
    :param command_options: The options that passes to command-line, e.g. -D, --class and --classpath.
    :param jobs_info_poll_interval: Seconds to wait between polls of job status in application mode (Default: 1)
    """

    def __init__(self,
                 name: str,
                 application: str,
                 target: Optional[str] = None,
                 application_args: Optional[List[Any]] = None,
                 executable_path: Optional[str] = None,
                 application_mode: bool = False,
                 stop_with_savepoint: bool = False,
                 kubernetes_cluster_id: Optional[str] = None,
                 command_options: Optional[str] = None,
                 jobs_info_poll_interval: int = 1,
                 **kwargs):
        super().__init__(name, **kwargs)
        self._application = application
        self._application_args = application_args
        self._executable_path = executable_path
        self._application_mode = application_mode
        self._target = target
        self._stop_with_savepoint = stop_with_savepoint
        self._kubernetes_cluster_id = kubernetes_cluster_id
        self._command_options = command_options
        self._jobs_info_poll_interval = jobs_info_poll_interval

        self._flink_run_cmd = None
        self._process = None
        self._flink_job_id = None
        self._yarn_application_id = None

        self._yarn_application_final_status = 'UNDEFINED'
        self._k8s_application_job_status = None

        self._is_yarn_application_mode = False
        self._is_kubernetes_application_mode = False
        self._is_yarn_per_job = False
        self._is_yarn_session = False
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

        if self._is_yarn_application_mode:
            self._start_tracking_yarn_application_status()
            if self._yarn_application_final_status != "SUCCEEDED":
                raise AIFlowException(
                    f"Yarn application {self._yarn_application_id} "
                    f"exited with status {self._yarn_application_final_status}"
                )
        elif self._is_kubernetes_application_mode:
            self.log.warning("Please be aware that the flink configuration "
                             "`execution.shutdown-on-application-finish` need to be set to `false`, "
                             "otherwise aiflow cannot check job status after finished.")
            self._retrieve_job_id_in_application_mode()
            self._start_tracking_k8s_application_status()
            if self._k8s_application_job_status != "FINISHED":
                raise AIFlowException(
                    f"Kubernetes application mode job {self._flink_job_id} "
                    f"exited with status {self._k8s_application_job_status}"
                )

    def stop(self, context: Context):
        if self._process and self._process.poll() is None:
            self._process.kill()

        kill_cmd = [self._get_executable_path()]
        if self._stop_with_savepoint:
            kill_cmd += ["stop"]
        else:
            kill_cmd += ["cancel"]

        if self._is_yarn_session or self._is_yarn_per_job:
            kill_cmd += ["-yid", self._yarn_application_id]
        elif self._is_yarn_application_mode:
            self._retrieve_job_id_in_application_mode()
            kill_cmd += ["-t", "yarn-application", f"-Dyarn.application.id={self._yarn_application_id}"]
        elif self._is_kubernetes_session:
            kill_cmd += ["-t", "kubernetes-session", f"-Dkubernetes.cluster-id={self._kubernetes_cluster_id}"]
        elif self._is_kubernetes_application_mode:
            kill_cmd += ["-t", "kubernetes-application", f"-Dkubernetes.cluster-id={self._kubernetes_cluster_id}"]
        elif self._target != 'local':
            kill_cmd += ["-t", self._target]

        if not self._flink_job_id:
            raise AIFlowException('Flink job id has not been obtained.')
        else:
            kill_cmd += [self._flink_job_id]

        self.log.info(f"Stopping task with command: {kill_cmd}")
        kill_process = subprocess.Popen(
            kill_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
        )
        stdout, stderr = kill_process.communicate()
        return_code = kill_process.wait()

        if self._is_kubernetes_application_mode:
            self._delete_cluster_in_k8s_application()

        if return_code:
            raise AIFlowException(
                "Failed to stop flink task. Error code: {}. Stdout: {}. Stderr: {}".format(
                    return_code, stdout, stderr
                )
            )

    def _validate_parameters(self):
        if self._application_mode:
            if self._target == "yarn-application":
                self._is_yarn_application_mode = True
                if not shutil.which("yarn"):
                    raise AIFlowException("Yarn application mode job tracking requires `yarn` installed.")
            elif self._target == "kubernetes-application":
                self._is_kubernetes_application_mode = True
                if not self._kubernetes_cluster_id:
                    raise AIFlowException(
                        'Param kubernetes_cluster_id must be set with kubernetes resource manager.'
                    )
                if not shutil.which("kubectl"):
                    raise AIFlowException("Kubernetes application mode job tracking requires `kubectl` installed.")
            else:
                raise AIFlowException(
                    f'Invalid --target option: {self._target} set to `flink run-application`'
                )
        else:
            if self._target is None or self._target in ['local', 'remote']:
                pass
            elif self._target == 'yarn-per-job':
                self._is_yarn_per_job = True
            elif self._target == 'yarn-session':
                self._is_yarn_session = True
            elif self._target == 'kubernetes-session':
                self._is_kubernetes_session = True
                if not self._kubernetes_cluster_id:
                    raise AIFlowException(
                        'Param kubernetes_cluster_id must be set with kubernetes resource manager.'
                    )
            else:
                raise AIFlowException(
                    f'Invalid --target option: {self._target} set to `flink run`'
                )

    def _get_executable_path(self):
        if self._executable_path:
            executable = self._executable_path
        elif shutil.which('flink') is not None:
            executable = shutil.which('flink')
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
        if self._is_kubernetes_session:
            command += [f"-Dkubernetes.cluster-id={self._kubernetes_cluster_id}"]
        elif self._is_kubernetes_application_mode:
            command += [
                "-Dexecution.shutdown-on-application-finish=false",
                f"-Dkubernetes.cluster-id={self._kubernetes_cluster_id}"
            ]
        if self._command_options:
            command += self._command_options.split()

        command += [self._application]
        if self._application_args:
            command += self._application_args

        self.log.info("flink run cmd: %s", mask_cmd(command))
        return command

    def _start_tracking_yarn_application_status(self):
        """
        Polls the job status until job finished with yarn api.

        Yarn Final-State would always be UNDEFINED until application finished.
        """
        if not self._yarn_application_id:
            raise AIFlowException("Yarn application id has not been obtained.")
        while self._yarn_application_final_status == 'UNDEFINED':
            status_cmd = f"yarn application --status {self._yarn_application_id}".split()
            status_process = subprocess.Popen(
                status_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=-1,
                universal_newlines=True,
            )
            for line in iter(status_process.stdout):
                if "Final-State" in line:
                    self._yarn_application_final_status = line.split(":")[1].strip()
            status_process.wait()
            time.sleep(self._jobs_info_poll_interval)
        self.log.info(f"Yarn application status is {self._yarn_application_final_status}")

    def _start_tracking_k8s_application_status(self):
        """
        Polls the job status until job finished and delete the deployment for flink job.

        Possible status:

        INITIALIZING
            The job has been received by the Dispatcher, and is waiting for the job manager
            to receive leadership and to be created.
        CREATED
            Job is newly created, no task has started to run.
        RUNNING
            Some tasks are scheduled or running, some may be pending, some may be finished.
        FAILING
            The job has failed and is currently waiting for the cleanup to complete.
        FAILED
            The job has failed with a non-recoverable task failure.
        CANCELLING
            Job is being cancelled.
        CANCELED
            Job has been cancelled.
        FINISHED
            All of the job's tasks have successfully finished.
        RESTARTING
            The job is currently undergoing a reset and total restart.
        SUSPENDED
            The job has been suspended which means that it has been stopped
            but not been removed from a potential HA job store.
        RECONCILING
            The job is currently reconciling and waits for task execution report to recover state.
        """
        while self._k8s_application_job_status not in ["FAILED", "CANCELED", "FINISHED", "SUSPENDED"]:
            for line in iter(self._list_jobs()):
                line = line.strip()
                if re.search(r': ([a-z0-9]+) : ', line):
                    match_status = re.search(r'^\((.*)\)$', line.split()[-1])
                    if match_status:
                        self._k8s_application_job_status = match_status.group(1)
            time.sleep(self._jobs_info_poll_interval)
            self.log.info(f"Flink job status: {self._k8s_application_job_status}")
        self._delete_cluster_in_k8s_application()

    def _delete_cluster_in_k8s_application(self):
        delete_cmd = ['kubectl', 'delete', f'deployments/{self._kubernetes_cluster_id}']
        delete_process = subprocess.Popen(
            delete_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=-1,
            universal_newlines=True,
        )
        outputs = delete_process.stdout
        return_code = delete_process.wait()
        if return_code:
            for line in iter(outputs):
                self.log.info(line)
            raise AIFlowException(
                "Failed to delete deployment {} for job {}".format(
                    self._kubernetes_cluster_id, self._flink_job_id
                )
            )

    def _list_jobs(self):
        """
        Lists flink jobs in yarn application mode and kubernetes application mode.
        """
        list_job_cmd = [self._get_executable_path(), 'list', '-a']
        if self._is_yarn_application_mode:
            list_job_cmd += ['-t', 'yarn-application', f'-Dyarn.application.id={self._yarn_application_id}']
        elif self._is_kubernetes_application_mode:
            list_job_cmd += ['-t', 'kubernetes-application', f'-Dkubernetes.cluster-id={self._kubernetes_cluster_id}']

        retries = 0
        while retries < 10:
            list_process = subprocess.Popen(
                list_job_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=-1,
                universal_newlines=True,
            )
            outputs = list_process.stdout
            return_code = list_process.wait()
            if return_code:
                retries += 1
            else:
                return outputs
            time.sleep(self._jobs_info_poll_interval)
        for line in iter(outputs):
            self.log.info(line)
        raise AIFlowException(
            f"Failed to poll job status for 10 times: returncode = {return_code}"
        )

    def _retrieve_job_id_in_application_mode(self):
        job_id_found: bool = False
        while not job_id_found:
            for line in iter(self._list_jobs()):
                line = line.strip()
                match_job_id = re.search(r': ([a-z0-9]+) : ', line)
                if match_job_id:
                    self._flink_job_id = match_job_id.group(1)
                    self.log.info('Identified flink job id {}'.format(self._flink_job_id))
                    job_id_found = True

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

