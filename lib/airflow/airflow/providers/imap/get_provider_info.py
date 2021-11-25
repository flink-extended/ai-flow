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
def get_provider_info():
    return {
        'package-name': 'apache-airflow-providers-imap',
        'name': 'Internet Message Access Protocol (IMAP)',
        'description': '`Internet Message Access Protocol (IMAP) <https://tools.ietf.org/html/rfc3501>`__\n',
        'versions': ['1.0.0'],
        'integrations': [
            {
                'integration-name': 'Internet Message Access Protocol (IMAP)',
                'external-doc-url': 'https://tools.ietf.org/html/rfc3501',
                'tags': ['protocol'],
            }
        ],
        'sensors': [
            {
                'integration-name': 'Internet Message Access Protocol (IMAP)',
                'python-modules': ['airflow.providers.imap.sensors.imap_attachment'],
            }
        ],
        'hooks': [
            {
                'integration-name': 'Internet Message Access Protocol (IMAP)',
                'python-modules': ['airflow.providers.imap.hooks.imap'],
            }
        ],
        'hook-class-names': ['airflow.providers.imap.hooks.imap.ImapHook'],
    }
