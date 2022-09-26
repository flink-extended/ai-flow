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
import unittest
from unittest import mock
from tempfile import TemporaryDirectory

from ai_flow.common.configuration.configuration import Configuration, get_server_configuration, get_client_configuration
from ai_flow.common.configuration.helpers import write_default_config
from ai_flow.common.env import expand_env_var, get_aiflow_home
from ai_flow.common.exception.exceptions import AIFlowConfigException
from ai_flow.common.util.file_util import yaml_utils


class TestConfiguration(unittest.TestCase):

    def test_home_dir(self):
        with unittest.mock.patch.dict('os.environ'):
            if 'AIFLOW_HOME' in os.environ:
                del os.environ['AIFLOW_HOME']
            self.assertEqual(get_aiflow_home(), expand_env_var('~/aiflow'))

    def test_load_config(self):
        with TemporaryDirectory(prefix='test_config') as tmp_dir:
            temp_config_file = os.path.join(tmp_dir, 'test_configuration.yaml')
            test_str = '''
                string: aBC
                integer: 30
                boolean: TRue
                lists:
                - string: aBC
                  integer: 30
                - string: aBC
                  integer: 30
                parent:
                    son1:
                        grandson1: g1
                        grandson2: g2
                    son2: s1
            '''
            yaml_dict = yaml_utils.load_yaml_string(test_str)
            yaml_utils.dump_yaml_file(yaml_dict, temp_config_file)
            config = Configuration(temp_config_file)
            self.assertEqual(yaml_dict, config.as_dict())

        self.assertEqual(config.get('string'), 'aBC')
        self.assertEqual(config.get_str('string'), 'aBC')
        self.assertEqual(config.get_int('integer'), 30)
        self.assertTrue(config.get_bool('boolean'))
        self.assertEqual(len(config.get('lists')), 2)
        self.assertEqual(type(config.get('parent')), dict)
        self.assertEqual(type(config.get('parent').get('son1')), dict)
        self.assertEqual(config.get('parent').get('son1').get('grandson1'), 'g1')

    def test_non_exists_config(self):
        with TemporaryDirectory(prefix='test_config') as tmp_dir:
            temp_config_file = os.path.join(tmp_dir, 'test_configuration.yaml')
            test_str = '''
                integer: 30
                boolean: TRue
            '''
            yaml_dict = yaml_utils.load_yaml_string(test_str)
            yaml_utils.dump_yaml_file(yaml_dict, temp_config_file)
            config = Configuration(temp_config_file)
        with self.assertRaises(AIFlowConfigException):
            config.get('non-exists-key')
        self.assertEqual(config.get('non-exists-key', 'abc'), 'abc')
        with self.assertRaises(AIFlowConfigException):
            config.get_str('non-exists-key')
        self.assertEqual(config.get_str('non-exists-key', 'abc'), 'abc')
        with self.assertRaises(AIFlowConfigException):
            config.get_int('non-exists-key')
        self.assertEqual(config.get_int('non-exists-key', 3), 3)
        self.assertFalse(config.get_bool('non-exists-key', False))
        self.assertTrue(config.get_bool('non-exists-key', True))

    def test_invalid_parser(self):
        with TemporaryDirectory(prefix='test_config') as tmp_dir:
            temp_config_file = os.path.join(tmp_dir, 'test_configuration.yaml')
            test_str = '''
                string: aBC
                integer: 30
                boolean: TRue
            '''
            yaml_dict = yaml_utils.load_yaml_string(test_str)
            yaml_utils.dump_yaml_file(yaml_dict, temp_config_file)
            config = Configuration(temp_config_file)
        with self.assertRaises(AIFlowConfigException) as context:
            config.get_int('string')
            self.assertTrue('Failed to convert value to int' in context.exception)
        with self.assertRaises(AIFlowConfigException) as context:
            config.get_float('string')
            self.assertTrue('Failed to convert value to float' in context.exception)

    def test_expand_env_and_template(self):
        with TemporaryDirectory(prefix='test_config') as tmp_dir:
            temp_config_file = os.path.join(tmp_dir, 'test_configuration.yaml')
            test_str = '''log_dir: {AIFLOW_HOME}/logs'''
            with open(temp_config_file, 'w') as fd:
                fd.write(test_str)

            config = Configuration(temp_config_file)
        self.assertEqual(config.get_str('log_dir'), expand_env_var('~/aiflow/logs'))

    def test_get_default_configuration(self):
        with TemporaryDirectory(prefix='test_config') as tmp_dir:
            with unittest.mock.patch.dict('os.environ', AIFLOW_HOME=tmp_dir):

                write_default_config('aiflow_server.yaml')
                server_conf = get_server_configuration()
                self.assertEqual(server_conf.get_str('log_dir'), expand_env_var('~/aiflow/logs'))

                client_conf = get_client_configuration()
                self.assertTrue(os.path.isfile(os.path.join(tmp_dir, 'aiflow_client.yaml')))
                self.assertEqual(client_conf.get_str('server_address'), expand_env_var('localhost:50051'))
                root_dir = expand_env_var('~/aiflow/blob')
                self.assertEqual(client_conf.get('blob_manager').get('blob_manager_config'), {'root_directory': root_dir})
