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
import random
import re
import string
import unittest

from ai_flow.task_executor.kubernetes import helpers


class TestHelpers(unittest.TestCase):
    def test_replace_invalid_chars(self):
        self.assertEqual('abcd123',
                         helpers.replace_invalid_chars('a_b-c.d@1 2,3'))

    def test_make_safe_label_value(self):
        test_cases = []
        test_cases.extend(
            [(self._gen_random_string(seed, 200), self._gen_random_string(seed, 200)) for seed in range(100)]
        )
        for v1, v2 in test_cases:
            safe_v1 = helpers.make_safe_label_value(v1)
            assert self._is_safe_label_value(safe_v1)
            safe_v2 = helpers.make_safe_label_value(v2)
            assert self._is_safe_label_value(safe_v2)
            before = "workflow_execution_id"
            assert before == helpers.make_safe_label_value(before)

    @staticmethod
    def _gen_random_string(seed, str_len):
        char_list = []
        for char_seed in range(str_len):
            random.seed(str(seed) * char_seed)
            char_list.append(random.choice(string.printable))
        return ''.join(char_list)

    @staticmethod
    def _is_safe_label_value(value):
        regex = r'^[^a-z0-9A-Z]*|[^a-zA-Z0-9_\-\.]|[^a-z0-9A-Z]*$'
        return len(value) <= 63 and re.match(regex, value)
