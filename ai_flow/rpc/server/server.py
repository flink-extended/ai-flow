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
import asyncio
import functools
import inspect
import logging
import threading
from concurrent import futures

import grpc

from ai_flow.common.configuration import config_constants
from grpc import _common, _server
from grpc._cython.cygrpc import StatusCode
from grpc._server import _serialize_response, _status, _abort, _Context, _unary_request, \
    _select_thread_pool_for_behavior, _unary_response_in_pool

from ai_flow.common.util.db_util import session as db_session
from ai_flow.rpc.protobuf import scheduler_service_pb2_grpc
from ai_flow.rpc.service.scheduler_service import SchedulerService
from ai_flow.scheduler.timer import timer_instance

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class AIFlowServer(object):
    """
    Block/Async server of an AIFlow.
    """
    def __init__(self):
        self.executor = Executor(futures.ThreadPoolExecutor(max_workers=10))
        self.server = grpc.server(self.executor)
        self.scheduler_service = SchedulerService()
        scheduler_service_pb2_grpc.add_SchedulerServiceServicer_to_server(self.scheduler_service, self.server)
        self.server.add_insecure_port('[::]:{}'.format(config_constants.RPC_PORT))
        self._stop = threading.Event()

    def run(self, is_block=False):
        self.server.start()
        logging.info('AIFlow server started.')
        self.scheduler_service.start()
        timer_instance.start()
        if is_block:
            try:
                while not self._stop.is_set():
                    self._stop.wait(_ONE_DAY_IN_SECONDS)
            except KeyboardInterrupt:
                logging.info("received KeyboardInterrupt")
                self.stop()
        else:
            pass

    def stop(self):
        logging.info("stopping AIFlow server")
        self.scheduler_service.stop()
        self.server.stop(0)
        self.executor.shutdown()
        timer_instance.shutdown()
        db_session.Session.remove()
        self._stop.set()
        logging.info('AIFlow server stopped.')


def _loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    if not loop.is_running() or loop.is_closed():
        loop.run_forever()
    pending = asyncio.all_tasks(loop=loop)
    if pending:
        loop.run_until_complete(asyncio.gather(*pending))


class Executor(futures.Executor):
    def __init__(self, thread_pool, loop=None):
        super().__init__()
        self._shutdown = False
        self._thread_pool = thread_pool
        self._loop = loop or asyncio.get_event_loop()
        if not self._loop.is_running() or self._loop.is_closed():
            self._thread = threading.Thread(target=_loop, args=(self._loop,), daemon=True)
            self._thread.start()

    def submit(self, fn, *args, **kwargs):
        if self._shutdown:
            raise RuntimeError('Cannot schedule new futures after shutdown.')
        if not self._loop.is_running():
            raise RuntimeError('Loop must be started before any function could be submitted.')
        if inspect.iscoroutinefunction(fn):
            coroutine = fn(*args, **kwargs)
            return asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        else:
            func = functools.partial(fn, *args, **kwargs)
            return self._loop.run_in_executor(self._thread_pool, func)

    def shutdown(self, wait=True):
        self._shutdown = True
        if wait:
            self._thread_pool.shutdown()


async def _call_behavior_async(rpc_event, state, behavior, argument, request_deserializer):
    context = _Context(rpc_event, state, request_deserializer)
    try:
        return await behavior(argument, context), True
    except Exception as e:
        with state.condition_type:
            if e not in state.rpc_errors:
                logging.exception(e)
                _abort(state, rpc_event.operation_call, StatusCode.unknown, _common.encode(e))
        return None, False


async def _unary_response_in_pool_async(rpc_event, state, behavior, argument_thunk, request_deserializer,
                                        response_serializer):
    argument = argument_thunk()
    if argument is not None:
        response, proceed = await _call_behavior_async(rpc_event, state, behavior, argument, request_deserializer)
        if proceed:
            serialized_response = _serialize_response(rpc_event, state, response, response_serializer)
            if serialized_response is not None:
                _status(rpc_event, state, serialized_response)


def _handle_unary_unary(rpc_event, state, method_handler, default_thread_pool):
    unary_request = _unary_request(rpc_event, state, method_handler.request_deserializer)
    thread_pool = _select_thread_pool_for_behavior(method_handler.unary_unary, default_thread_pool)
    if asyncio.iscoroutinefunction(method_handler.unary_unary):
        return thread_pool.submit(_unary_response_in_pool_async, rpc_event, state, method_handler.unary_unary,
                                  unary_request, method_handler.request_deserializer,
                                  method_handler.response_serializer)
    else:
        return thread_pool.submit(_unary_response_in_pool, rpc_event, state, method_handler.unary_unary, unary_request,
                                  method_handler.request_deserializer, method_handler.response_serializer)


_server._handle_unary_unary = _handle_unary_unary
