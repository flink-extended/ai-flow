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
"""Event commands"""
import functools
from argparse import Namespace
from queue import Queue
from typing import Callable, TypeVar, cast, List

from notification_service.base_notification import EventWatcher, BaseEvent
from notification_service.client import NotificationClient
from notification_service.cli.simple_table import NotificationConsole


T = TypeVar("T", bound=Callable)  # pylint: disable=invalid-name


def action_logging(f: T) -> T:

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not args:
            raise ValueError("Args should be set")
        if not isinstance(args[0], Namespace):
            raise ValueError(
                "1st positional argument should be argparse. Namespace instance," f"but is {type(args[0])}"
            )

        if not args[0].server_uri:
            print("Argument --server-uri not set. See `notification event {} -h`".format(args[0].subcommand))
            return
        if not args[0].key:
            print("Argument --key not set. See `notification event {} -h`".format(args[0].subcommand))
            return
        return f(*args, **kwargs)

    return cast(T, wrapper)


@action_logging
def list_events(args):
    """List events at the command line"""
    client = NotificationClient(server_uri=args.server_uri)
    events = client.list_events(key=args.key,
                                namespace=args.namespace,
                                version=args.begin_version,
                                event_type=args.event_type,
                                start_time=args.begin_time,
                                sender=args.sender)
    NotificationConsole().print_as(
        data=events,
        output=args.output,
        mapper=lambda event: {
            "namespace": event.namespace,
            "key": event.key,
            "value": event.value,
            "event_type": event.event_type,
            "sender": event.sender,
            "create_time": event.create_time,
            "context": event.context,
            "version": event.version,
        },
    )


@action_logging
def count_events(args):
    """Count events at the command line"""
    client = NotificationClient(server_uri=args.server_uri)
    res = client.count_events(key=args.key,
                              namespace=args.namespace,
                              version=args.begin_version,
                              event_type=args.event_type,
                              start_time=args.begin_time,
                              sender=args.sender)
    print(res[0])


@action_logging
def listen_events(args):
    """Listen events at the command line"""
    class CliWatcher(EventWatcher):
        def __init__(self, queue):
            self.queue = queue

        def process(self, events: List[BaseEvent]):
            for e in events:
                self.queue.put(e)

    client = NotificationClient(server_uri=args.server_uri)
    event_queue = Queue()
    client.start_listen_event(key=args.key,
                              namespace=args.namespace,
                              version=args.begin_version,
                              event_type=args.event_type,
                              start_time=args.begin_time,
                              sender=args.sender,
                              watcher=CliWatcher(event_queue))
    try:
        while True:
            print(event_queue.get())
    except KeyboardInterrupt:
        pass


@action_logging
def send_event(args):
    """Send an event at the command line"""
    client = NotificationClient(server_uri=args.server_uri,
                                default_namespace=args.namespace,
                                sender=args.sender)
    if not args.value:
        print("Arguments --value not set. See `notification event send {} -h`")
    event = BaseEvent(
        key=args.key,
        value=args.value,
        event_type=args.event_type,
        context=args.context)
    client.send_event(event)
