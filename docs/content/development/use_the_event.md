# Using the Event

On behalf of [Notification Service](https://github.com/flink-extended/ai-flow/tree/master/lib/notification_service), AIFlow can send or receive messages to control the execution of jobs. More than that, users can also implement their own control semantics by sending custom events using Notification Service. This document will walk you through sending and receiving custom events.

## Event 

An event has the following fields that users can specified when creating an event.

* key: required,
* value: required, the actual event contents
* event_type: optional, the type of event which helps filter
* context: optional,

An event also has some metadata fields.

* version: 
* create_time: the timestamp of event creation
* namespace: 
* sender: the client who sent the event

## Notification Client

To send or receive events, you need a [Notification Client](https://github.com/flink-extended/ai-flow/blob/3b2a74e4d5579c9547dd24955b38ff83edd4dc6b/lib/notification_service/notification_service/client.py#L86). With the client, you can communicate with the notification server.

## Sending Events

Notification Client has a method to send the event.

```python
@abc.abstractmethod
    def send_event(self, event: BaseEvent):
        """
        Send event to Notification Service.

        :param event: the event updated.
        :return: The created event which has version and create time.
        """
        pass
```


## Receiving Events

Users can choose to list or to continuously listen for a certain type of event.

### Listing Events

Notification Client has the following methods to list events you needed.

```python
    @abc.abstractmethod
    def list_events(self,
                    key: Union[str, List[str]],
                    namespace: str = None,
                    version: int = None,
                    event_type: str = None,
                    start_time: int = None,
                    sender: str = None) -> List[BaseEvent]:
        """
        List specific events in Notification Service.

        :param key: Key of the event for listening.
        :param namespace: Namespace of the event for listening.
        :param version: (Optional) The version of the events must greater than this version.
        :param event_type: (Optional) Type of the events.
        :param start_time: (Optional) Start time of the events.
        :param sender: The event sender.
        :return: The event list.
        """
        pass

    @abc.abstractmethod
    def list_all_events(self,
                        start_time: int = None,
                        start_version: int = None,
                        end_version: int = None) -> List[BaseEvent]:
        """
        List specific `key` or `version` of events in Notification Service.

        :param start_time: (Optional) Start time of the events.
        :param start_version: (Optional) the version of the events must greater than the
                              start_version.
        :param end_version: (Optional) the version of the events must equal or less than the
                            end_version.
        :return: The event list.
        """
        pass
       
```

### Listening Events

You can continuously listen for a certain type of event by following method:

```python
    @abc.abstractmethod
    def start_listen_event(self,
                           key: Union[str, Tuple[str]],
                           watcher: EventWatcher,
                           namespace: str = None,
                           version: int = None,
                           event_type: str = None,
                           start_time: int = None,
                           sender: str = None) -> EventWatcherHandle:
        """
        Start listen specific `key` or `version` notifications in Notification Service.

        :param key: Key of notification for listening.
        :param namespace: Namespace of the event for listening.
        :param watcher: Watcher instance for listening.
        :param version: (Optional) The version of the events must greater than this version.
        :param event_type: (Optional) Type of the events for listening.
        :param start_time: (Optional) Start time of the events for listening.
        :param sender: The event sender.
        :return: The handle used to stop the listening.
        """
        pass
```

After receiving the event you are interested in,  you may want to perform some associated processing logic, so an EventWatcher need to be passed. You need to create your own EventWatcher by implementing the `process` function. The `process` function takes a list of events and every batch of events would be processed with this function.

```python
class EventWatcher(metaclass=abc.ABCMeta):
    """
    SignalWatcher is used to represent a standard event handler, which defines the
    logic related to signal notifications.
    """

    @abc.abstractmethod
    def process(self, events: List[BaseEvent]):
        pass
```



