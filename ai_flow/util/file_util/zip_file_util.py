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
import zipfile
import time
import fcntl
from pathlib import Path
from typing import Text


def make_dir_zipfile(source_dir, output_filename):
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename): # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)


def make_file_zipfile(source_file, output_filename):
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.write(source_file, os.path.basename(source_file))


def extract_zip_file(zip_file_path: Text,
                     extract_path: Text = None) -> str:
    """
    :param zip_file_path: The zip file path.
    :param extract_path: The decompression path of the project zip file. If None,
                         extract to the same directory as zip_file_path.
    :return: The project path.
    """
    file_dir = os.path.dirname(zip_file_path)
    file_name = os.path.basename(zip_file_path)
    lock_file = os.path.join(file_dir, '{}.lock'.format(file_name))

    dest_path = file_dir if extract_path is None else extract_path

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        top_dir = os.path.split(zip_ref.namelist()[0])[0]
        downloaded_local_path = str(Path(dest_path) / top_dir)
        if os.path.exists(lock_file):
            while os.path.exists(lock_file):
                time.sleep(1)
            return downloaded_local_path
        else:
            if not os.path.exists(downloaded_local_path):
                f = open(lock_file, 'w')
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    if not os.path.exists(downloaded_local_path):
                        zip_ref.extractall(dest_path)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                f.close()
                try:
                    os.remove(lock_file)
                except OSError:
                    pass
            return downloaded_local_path
