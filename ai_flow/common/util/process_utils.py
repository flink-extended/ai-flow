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
import logging
import os
import signal
import time

import psutil
from typing import List

logger = logging.getLogger(__name__)


def get_all_children_pids(current_pid=None) -> List:
    result = []
    if not psutil.pid_exists(current_pid):
        return result
    p = psutil.Process(current_pid)
    for pp in p.children():
        result.append(pp.pid)
        result.extend(get_all_children_pids(pp.pid))
    return result


def check_pid_exist(_pid):
    try:
        os.kill(_pid, 0)
    except OSError:
        return False
    else:
        return True


def stop_process(pid, timeout_sec: int = 60):
    """
    Try hard to kill the process with the given pid. It sends
    :param pid: The process pid to stop
    :param timeout_sec: timeout before sending SIGKILL to kill the process
    """

    try:
        os.kill(pid, signal.SIGTERM)
        start_time = time.monotonic()
        while check_pid_exist(pid):
            if time.monotonic() - start_time > timeout_sec:
                raise RuntimeError(
                    "pid: {} does not exit after {} seconds.".format(pid, timeout_sec))
            time.sleep(1)
    except ProcessLookupError:
        pass
    except Exception:
        logger.warning("Failed to stop pid: {} with SIGTERM. Try to send SIGKILL".format(pid))
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception as e:
            raise RuntimeError("Failed to kill pid: {} with SIGKILL.".format(pid)) from e

    logger.info("pid: {} stopped".format(pid))
