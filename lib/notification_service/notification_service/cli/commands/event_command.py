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
"""Event commands"""
import functools
from argparse import Namespace
from datetime import datetime as dt
from queue import Queue
from typing import Callable, TypeVar, cast, List

from notification_service.client.embedded_notification_client import EmbeddedNotificationClient
from notification_service.client.notification_client import ListenerProcessor
from notification_service.model.event import Event

from ai_flow.common.util import time_utils
from notification_service.cli.simple_table import NotificationConsole


T = TypeVar("T", bound=Callable)  # pylint: disable=invalid-name


def check_arguments(f: T) -> T:

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not args:
            raise ValueError("Args should be set")
        if not isinstance(args[0], Namespace):
            raise ValueError(
                "1st positional argument should be argparse.Namespace instance," f"but is {type(args[0])}."
            )

        if not args[0].server_uri:
            print("Argument --server-uri is not set. See `notification event {} -h`".format(args[0].subcommand))
            return
        return f(*args, **kwargs)

    return cast(T, wrapper)


@check_arguments
def list_events(args):
    """List events at the command line"""
    client = EmbeddedNotificationClient(server_uri=args.server_uri)
    offset = 0
    if args.begin_offset:
        offset = args.begin_offset
    elif args.begin_time:
        offset = client.time_to_offset(time_utils.timestamp_to_datetime(args.begin_time))
    events = client.list_events(key=args.key,
                                namespace=args.namespace,
                                sender=args.sender,
                                begin_offset=offset)
    NotificationConsole().print_as(
        data=events,
        output=args.output,
        mapper=lambda event: {
            "namespace": event.namespace,
            "key": event.key,
            "value": event.value,
            "sender": event.sender,
            "create_time": dt.fromtimestamp(event.create_time/1000).isoformat(),
            "context": event.context,
            "offset": event.offset,
        },
    )


@check_arguments
def count_events(args):
    """Count events at the command line"""
    client = EmbeddedNotificationClient(server_uri=args.server_uri)
    offset = 0
    if args.begin_offset:
        offset = args.begin_offset
    elif args.begin_time:
        offset = client.time_to_offset(time_utils.timestamp_to_datetime(args.begin_time))
    res = client.count_events(key=args.key,
                              namespace=args.namespace,
                              sender=args.sender,
                              begin_offset=offset)
    print(res[0])


@check_arguments
def listen_events(args):
    """Listen events at the command line"""
    class Processor(ListenerProcessor):
        def __init__(self, queue):
            self.queue = queue

        def process(self, events: List[Event]):
            for e in events:
                self.queue.put(e)

    client = EmbeddedNotificationClient(server_uri=args.server_uri,
                                        namespace=args.namespace)

    offset = 0
    if args.begin_offset:
        offset = args.begin_offset
    elif args.begin_time:
        offset = client.time_to_offset(time_utils.timestamp_to_datetime(args.begin_time))

    event_queue = Queue()
    registration_id = client.register_listener(listener_processor=Processor(event_queue),
                                               event_keys=[args.key, ],
                                               offset=offset)

    try:
        while True:
            print(event_queue.get())
    except KeyboardInterrupt:
        pass
    finally:
        client.unregister_listener(registration_id)


@check_arguments
def send_event(args):
    """Send an event at the command line"""
    client = EmbeddedNotificationClient(server_uri=args.server_uri,
                                        namespace=args.namespace,
                                        sender=args.sender)
    event = Event(
        key=args.key,
        value=args.value
    )
    event: Event = client.send_event(event)
    print("Successfully send event: {}.".format(event))
