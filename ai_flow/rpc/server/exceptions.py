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
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.rpc.protobuf.message_pb2 import INTERNAL_ERROR


class AIFlowRpcServerException(AIFlowException):
    """
    Generic exception thrown to surface failure information about external-facing operations.
    The error message associated with this exception may be exposed to clients in HTTP responses
    for debugging purposes. If the error text is sensitive, raise a generic `Exception` object
    instead.
    """

    def __init__(self, error_msg, error_code=INTERNAL_ERROR, **kwargs):
        """
        :param message: The message describing the error that occurred. This will be included in the
                        exception's serialized JSON representation.
        :param error_code: An appropriate error code for the error that occurred; it will be included
                           in the exception's serialized JSON representation.
        :param kwargs: Additional key-value pairs to include in the serialized JSON representation
                       of the AIFlowException.
        """
        try:
            self.error_code = error_code
        except (ValueError, TypeError):
            self.error_code = INTERNAL_ERROR
        self.error_msg = error_msg
        self.json_kwargs = kwargs
        super(AIFlowException, self).__init__(error_msg)
