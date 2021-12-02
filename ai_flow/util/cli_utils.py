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
"""Utilities module for cli"""

import functools
from typing import Callable, TypeVar, cast

from ai_flow.context.project_context import init_project_context

T = TypeVar("T", bound=Callable)  # pylint: disable=invalid-name


def init_config(f: T) -> T:
    """
    Decorates function to execute function at the same time submitting init_config
    but in CLI context.

    :param f: function instance
    :return: wrapped function
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        """
        An wrapper for cli functions. It assumes to have Namespace instance
        at 1st positional argument

        :param args: Positional argument. It assumes to have Namespace instance
            at 1st positional argument
        :param kwargs: A passthrough keyword argument
        """
        init_project_context(args[0].project_path)
        return f(*args, **kwargs)

    return cast(T, wrapper)
