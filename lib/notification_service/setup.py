# coding:utf-8
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
import sys
import time

from setuptools import setup, find_packages

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
nightly_build = os.getenv('NIGHTLY_BUILD') == 'true'


def get_script():
    bin_dir = os.path.join(CURRENT_DIR, "bin")
    return [os.path.join("bin", filename) for filename in os.listdir(bin_dir)]


version_file = os.path.join(CURRENT_DIR, 'notification_service/version.py')
try:
    exec(open(version_file).read())
except IOError:
    print("Failed to load notification_service version file for packaging. " +
          "'%s' not found!" % version_file,
          file=sys.stderr)
    sys.exit(-1)
VERSION = time.strftime('%Y.%m.%d', time.localtime(time.time())) if nightly_build else __version__ # noqa
PACKAGE_NAME = 'notification_service_nightly' if nightly_build else 'notification_service'


require_file = '{}/{}'.format(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
with open(require_file) as f:
    context = f.read()
    require_file_lines = context.strip().split('\n')

require_packages = []
for line in require_file_lines:
    if not len(line.strip()) == 0 and not line.startswith("#"):
        require_packages.append(line)

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description='A Python package which provides stable notification service.',
    author='',
    author_email='flink.aiflow@gmail.com',
    url='https://github.com/flink-extended/ai-flow',
    packages=find_packages(exclude=['tests*']),
    scripts=get_script(),
    package_data={'notification_service': ['alembic.ini']},
    include_package_data=True,
    install_requires=require_packages,
    entry_points={
        'console_scripts': [
            'notification = notification_service.__main__:main'
        ]
    }
)
