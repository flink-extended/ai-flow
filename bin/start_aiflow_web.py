#!/usr/bin/env python
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
import signal
import logging

from subprocess import Popen

import ai_flow


def stop_web(signum, frame):
    global sub_process
    if sub_process:
        try:
            sub_process.terminate()
        except Exception as e:
            logging.error("Fail to terminate process pid: {}, killing the process with SIGKILL"
                          .format(sub_process.pid), exc_info=e)
        finally:
            sub_process.kill()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, stop_web)
    if "AIFLOW_HOME" not in os.environ:
        os.environ["AIFLOW_HOME"] = os.environ["HOME"] + "/aiflow"
        logging.info("Set env variable AIFLOW_HOME to {}".format(os.environ["AIFLOW_HOME"]))

    aiflow_web_command = ['python', ai_flow.frontend.web_server.__file__,
                          '-c', os.path.join(os.environ["AIFLOW_HOME"], 'aiflow_server.yaml')]
    sub_process = Popen(aiflow_web_command)
    sub_process.wait()
