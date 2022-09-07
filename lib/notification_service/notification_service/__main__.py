#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
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

"""Main executable module"""

import argcomplete

from notification_service.cli import cli_parser


def main():
    """Main executable function"""

    parser = cli_parser.get_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
