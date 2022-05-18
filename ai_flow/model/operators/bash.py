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
import logging
import os
import signal
import threading
from subprocess import Popen, STDOUT, TimeoutExpired, PIPE
from tempfile import TemporaryDirectory
from typing import Dict, Optional

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.thread_utils import StoppableThread
from ai_flow.model.context import Context
from ai_flow.model.operator import AIFlowOperator
from ai_flow.model.status import TaskStatus

logger = logging.getLogger(__name__)


class BashOperator(AIFlowOperator):

    def __init__(self,
                 name: str,
                 bash_command: str,
                 **kwargs):
        super().__init__(name, **kwargs)
        self.bash_command = bash_command
        self.sub_process = None
        self.log_reader = StoppableThread(target=self._read_output)

    def start(self, context: Context):
        with TemporaryDirectory(prefix='aiflow_tmp') as tmp_dir:
            def pre_exec():
                # Restore default signal disposition and invoke setsid
                for sig in ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ'):
                    if hasattr(signal, sig):
                        signal.signal(getattr(signal, sig), signal.SIG_DFL)
                os.setsid()

            logger.info('Running command: %s', self.bash_command)
            self.sub_process = Popen(
                ['bash', "-c", self.bash_command],
                stdout=PIPE,
                stderr=STDOUT,
                cwd=tmp_dir,
                preexec_fn=pre_exec,
            )
        self.log_reader.start()

    def stop(self, context: Context):
        logger.info('Sending SIGTERM signal to bash process group')
        try:
            if self.sub_process and hasattr(self.sub_process, 'pid'):
                os.killpg(os.getpgid(self.sub_process.pid), signal.SIGTERM)
        finally:
            # Need to call sub_process.wait() to avoid becoming zombie processes
            self.sub_process.wait()
            self.log_reader.stop()

    def await_termination(self, context: Context, timeout: Optional[int] = None):
        try:
            self.sub_process.wait(timeout=timeout)

            logger.info('Command exited with return code %s', self.sub_process.returncode)

            if self.sub_process.returncode != 0:
                raise AIFlowException('Bash command failed. The command returned a non-zero exit code.')
        except TimeoutExpired:
            logger.error("Timeout to wait bash operator to be finished in {} seconds".format(timeout))
            raise
        finally:
            self.log_reader.stop()

    def get_status(self, context: Context) -> TaskStatus:
        pass

    def get_metrics(self, context: Context) -> Dict:
        pass

    def _read_output(self):
        logger.info('Output:')
        for raw_line in iter(self.sub_process.stdout.readline, b''):
            if not threading.current_thread().stopped():
                line = raw_line.decode('utf-8').rstrip()
                logger.info("%s", line)
