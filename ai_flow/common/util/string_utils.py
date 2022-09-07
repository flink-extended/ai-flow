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
import re
from typing import Union, List

# 7-bit C1 ANSI escape sequences
ANSI_ESCAPE = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')


def remove_escape_codes(text: str) -> str:
    """
    Remove ANSI escapes codes from string. It's used to remove
    "colors" from log messages.
    """
    return ANSI_ESCAPE.sub("", text)


def mask_cmd(cmd: Union[str, List[str]]) -> str:
    cmd_masked = re.sub(
        r"("
        r"\S*?"  # Match all non-whitespace characters before...
        r"(?:secret|password)"  # ...literally a "secret" or "password"
        # word (not capturing them).
        r"\S*?"  # All non-whitespace characters before either...
        r"(?:=|\s+)"  # ...an equal sign or whitespace characters
        # (not capturing them).
        r"(['\"]?)"  # An optional single or double quote.
        r")"  # This is the end of the first capturing group.
        r"(?:(?!\2\s).)*"  # All characters between optional quotes
        # (matched above); if the value is quoted,
        # it may contain whitespace.
        r"(\2)",  # Optional matching quote.
        r'\1******\3',
        ' '.join(cmd),
        flags=re.I,
    )
    return cmd_masked