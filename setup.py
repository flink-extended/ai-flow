# coding:utf-8
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
import subprocess
import sys
from shutil import copytree, rmtree
from setuptools import setup, find_packages
from typing import Dict, List

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
in_source = os.path.isfile(CURRENT_DIR + "/run_tests.sh")

devel = [
    'coverage>=6.1.1',
    'flake8',
    'pytest',
    'mock',
]
mysql = [
    'pymysql==0.9.3',
    'mysqlclient>=1.3.6,<1.4',
]
celery = [
    'apache-airflow-providers-celery==1.0.1',
    'redis~=3.2',
]
hdfs = [
    'hdfs~=2.6.0',
]
oss = [
    'oss2==2.9.1',
]
s3 = [
    'boto3~=1.19.7',
    'botocore~=1.22.7',
]
mongo = [
    'mongoengine~=0.22.1',
]
example_requires = [
    'joblib==1.0.1',
    'numpy==1.18.1',
    'pandas==0.24.2',
    'scikit-learn==0.21.2',
]
flink = [
    'apache-flink==1.12.5',
]

devel = devel + mongo + mysql + oss + s3 + hdfs + flink

EXTRAS_REQUIREMENTS: Dict[str, List[str]] = {
    'devel': devel,
    'mysql': mysql,
    'celery': celery,
    'hdfs': hdfs,
    'oss': oss,
    'mongo': mongo,
    'example_requires': example_requires,
}


def remove_if_exists(file_path):
    if os.path.exists(file_path):
        if os.path.islink(file_path) or os.path.isfile(file_path):
            os.remove(file_path)
        else:
            assert os.path.isdir(file_path)
            rmtree(file_path)


def remove_installed_airflow():
    from distutils.sysconfig import get_python_lib

    local_site_package = get_python_lib()
    installed_airflow_path = os.path.join(local_site_package, "airflow")
    for file in os.listdir(installed_airflow_path):
        abs_path = os.path.join(installed_airflow_path, file)
        if os.path.isdir(abs_path) and file == 'providers':
            print("Airflow providers are not being removed.")
        else:
            remove_if_exists(abs_path)

def compile_frontend():  # noqa
    # """Run a command to compile and build aiflow frontend."""
    subprocess.check_call('./ai_flow/frontend/compile_frontend.sh')


def compile_assets():  # noqa
    # """Run a command to compile and build airflow assets."""
    subprocess.check_call('./lib/airflow/airflow/www/compile_assets.sh')


def get_script():
    bin_dir = os.path.join(CURRENT_DIR, "bin")
    return [os.path.join("bin", filename) for filename in os.listdir(bin_dir)]


version_file = os.path.join(CURRENT_DIR, 'ai_flow/version.py')
try:
    exec(open(version_file).read())
except IOError:
    print("Failed to load ai_flow version file for packaging. " +
          "'%s' not found!" % version_file,
          file=sys.stderr)
    sys.exit(-1)
VERSION = __version__ # noqa


try:
    if in_source:
        if os.getenv('INSTALL_AIRFLOW_WITHOUT_FRONTEND') != 'true':
            compile_assets()
        AIRFLOW_DIR = CURRENT_DIR + "/lib/airflow"
        try:
            os.symlink(AIRFLOW_DIR + "/airflow", CURRENT_DIR + "/airflow")
        except BaseException:  # pylint: disable=broad-except
            copytree(AIRFLOW_DIR + "/airflow", CURRENT_DIR + "/airflow")
    else:
        remove_installed_airflow()

    if os.getenv('INSTALL_AIFLOW_WITHOUT_FRONTEND') != 'true':
        compile_frontend()

    require_file = '{}/{}'.format(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    with open(require_file) as f:
        context = f.read()
        require_file_lines = context.strip().split('\n')
    require_packages = ['notification-service=={}'.format(VERSION)]

    for line in require_file_lines:
        if os.getenv('BUILD_MINI_AI_FLOW_PACKAGE') == 'true' and line.startswith("# Optional"):
            break
        if not len(line.strip()) == 0 and not line.startswith("#"):
            require_packages.append(line)

    packages = find_packages()
    setup(
        name='ai_flow',
        version=VERSION,
        description='An open source framework that bridges big data and AI.',
        author='',
        author_email='flink.aiflow@gmail.com',
        url='https://github.com/flink-extended/ai-flow',
        packages=find_packages(),
        install_requires=require_packages,
        extras_require=EXTRAS_REQUIREMENTS,
        python_requires='>=3.6, <3.8' if os.getenv('BUILD_MINI_AI_FLOW_PACKAGE') == 'true' else '>=3.7, <3.8',
        include_package_data=True,
        scripts=get_script(),
        package_data={'ai_flow': ['alembic.ini']},
        entry_points={
            'console_scripts': [
                'aiflow = ai_flow.__main__:main'
            ]
        }
    )
finally:
    if in_source:
        remove_if_exists(CURRENT_DIR + "/airflow")
