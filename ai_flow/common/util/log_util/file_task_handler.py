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
"""File logging handler for tasks."""
import logging
import os
from pathlib import Path
from jinja2 import Template


class FileTaskHandler(logging.Handler):

    def __init__(self, base_log_folder: str, filename_template: str):
        super().__init__()
        self.handler = None
        self.local_base = base_log_folder
        self.filename_jinja_template = Template(filename_template)

    def set_context(self, workflow_name: str, task_execution_key):
        local_loc = self._init_file(workflow_name, task_execution_key)
        self.handler = logging.FileHandler(local_loc, encoding='utf-8')
        if self.formatter:
            self.handler.setFormatter(self.formatter)
        self.handler.setLevel(self.level)

    def emit(self, record):
        if self.handler:
            self.handler.emit(record)

    def flush(self):
        if self.handler:
            self.handler.flush()

    def close(self):
        if self.handler:
            self.handler.close()

    def _render_filename(self, workflow_name, key):
        jinja_context = {
            'workflow_name': workflow_name,
            'execution_id': key.workflow_execution_id,
            'task_name': key.task_name,
            'seq_number': key.seq_num,
        }
        return self.filename_jinja_template.render(**jinja_context)

    def _init_file(self, workflow_name, task_execution_key):
        relative_path = self._render_filename(workflow_name, task_execution_key)
        full_path = os.path.join(self.local_base, relative_path)
        directory = os.path.dirname(full_path)
        Path(directory).mkdir(mode=0o777, parents=True, exist_ok=True)

        if not os.path.exists(full_path):
            open(full_path, "a").close()
            try:
                os.chmod(full_path, 0o666)
            except OSError:
                logging.warning("OSError while change ownership of the log file")
        return full_path
