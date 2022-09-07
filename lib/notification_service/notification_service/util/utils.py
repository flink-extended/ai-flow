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
import logging
import os
import signal
import socket
import time
from importlib import import_module
from itertools import tee, filterfalse

import dateutil.parser
from typing import Callable, Iterable

from notification_service.model.event import Event
from notification_service.model.member import Member
from notification_service.model.sender_event_count import SenderEventCount
from notification_service.rpc.protobuf import notification_service_pb2

if not hasattr(time, 'time_ns'):
    time.time_ns = lambda: int(time.time() * 1e9)

logger = logging.getLogger(__name__)


def event_to_proto(event: Event):
    result_event_proto = notification_service_pb2.EventProto(key=event.key,
                                                             offset=event.offset,
                                                             value=event.value,
                                                             create_time=event.create_time,
                                                             namespace=event.namespace,
                                                             context=event.context,
                                                             sender=event.sender)
    return result_event_proto


def count_to_proto(count: SenderEventCount):
    sender_event_count_proto = notification_service_pb2.SenderEventCountProto(sender=count.sender,
                                                                              event_count=count.event_count)
    return sender_event_count_proto


def event_list_to_proto(event_list):
    event_proto_list = []
    for event_model in event_list:
        event_proto = event_to_proto(event_model)
        event_proto_list.append(event_proto)
    return event_proto_list


def count_list_to_proto(count_list):
    event_count = 0
    count_proto_list = []
    for count in count_list:
        event_count += count.event_count
        count_proto_list.append(count_to_proto(count))
    return event_count, count_proto_list


def event_proto_to_event(event_proto):
    event = Event(key=event_proto.key, value=event_proto.value)
    event.namespace = event_proto.namespace
    event.sender = event_proto.sender
    event.context = event_proto.context
    event.offset = event_proto.offset
    event.create_time = event_proto.create_time
    return event


def event_count_proto_to_event_count(event_count_proto):
    return SenderEventCount(sender=event_count_proto.sender,
                            event_count=event_count_proto.event_count)


def event_model_to_event(event_model):
    event = Event(key=event_model.key, value=event_model.value)
    event.namespace = event_model.namespace
    event.sender = event_model.sender
    event.offset = event_model.offset
    event.create_time = event_model.create_time
    event.context = event_model.context
    return event


def count_result_to_sender_event_count(count_result):
    return SenderEventCount(
        sender=count_result.sender,
        event_count=count_result.event_count
    )


def member_to_proto(member: Member):
    return notification_service_pb2.MemberProto(
        version=member.version, server_uri=member.server_uri, update_time=member.update_time)


def proto_to_member(member_proto):
    return Member(member_proto.version, member_proto.server_uri, member_proto.update_time)


def sleep_and_detecting_running(interval_ms, is_running_callable, min_interval_ms=500):
    start_time = time.monotonic() * 1000
    while is_running_callable() and time.monotonic() * 1000 < start_time + interval_ms:
        remaining = time.monotonic() * 1000 - start_time
        if remaining > min_interval_ms:
            time.sleep(min_interval_ms / 1000)
        else:
            time.sleep(remaining / 1000)


def get_ip_addr() -> str:
    """
    Get ip address of localhost by UDP socket.
    :return: ip address of localhost
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = '127.0.0.1'
    finally:
        s.close()
        return ip


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        raise ImportError(f"{dotted_path} doesn't look like a module path")

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        raise ImportError(f'Module "{module_path}" does not define a "{class_name}" attribute/class')


def partition(pred: Callable, iterable: Iterable):
    """Use a predicate to partition entries into false entries and true entries"""
    iter_1, iter_2 = tee(iterable)
    return filterfalse(pred, iter_1), filter(pred, iter_2)


def parse_date(dt: str):
    """
    Parse a datetime in ISO 8601 to milliseconds since epoch.

    :param dt: datetime string
    """
    parsed_time = dateutil.parser.parse(dt)
    return int(parsed_time.timestamp() * 1000)


def check_pid_exist(_pid):
    try:
        os.kill(_pid, 0)
    except OSError:
        return False
    else:
        return True


def stop_process(pid, process_name, timeout_sec: int = 60):
    """
    Try hard to kill the process with the given pid. It sends
    :param pid: The process pid to stop
    :param process_name: The process name to log
    :param timeout_sec: timeout before sending SIGKILL to kill the process
    """

    try:
        start_time = time.monotonic()
        while check_pid_exist(pid):
            if time.monotonic() - start_time > timeout_sec:
                raise RuntimeError(
                    "{} pid: {} does not exit after {} seconds.".format(process_name, pid, timeout_sec))
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
    except Exception:
        logger.warning("Failed to stop {} pid: {} with SIGTERM. Try to send SIGKILL".format(process_name, pid))
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception as e:
            raise RuntimeError("Failed to kill {} pid: {} with SIGKILL.".format(process_name, pid)) from e

    logger.info("{} pid: {} stopped".format(process_name, pid))
