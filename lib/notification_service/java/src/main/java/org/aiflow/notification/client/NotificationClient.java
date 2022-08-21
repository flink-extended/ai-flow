package org.aiflow.notification.client;

import org.aiflow.notification.entity.EventKey;
import org.aiflow.notification.entity.EventMeta;

import java.util.List;

public abstract class NotificationClient {

    /**
     * Send the event to Notification Service.
     *
     * @param event The event to be sent.
     * @return Object of Event created in Notification Service.
     */
    protected abstract EventMeta sendEvent(EventMeta event) throws Exception;

    /**
     * Register a listener to start listen specific events in Notification Service.
     *
     * @param listenerProcessor Namespace of notification for listening.
     * @param eventKeys Keys of events for listening.
     * @param offset Start offset of notification for listening.
     */
    protected abstract ListenerRegistrationId registerListener(
            ListenerProcessor listenerProcessor, List<EventKey> eventKeys, Long offset);

    /**
     * * Unregister the listener by id.
     *
     * @param id The ListenerRegistrationId
     */
    protected abstract void unRegisterListener(ListenerRegistrationId id);

    /**
     * List specific events in Notification Service.
     *
     * @param event_name Name of events to be listed, null indicates not filter by name.
     * @param namespace Namespace of events to be listed, null indicates not filter by namespace.
     * @param eventType Type of events to be listed, null indicates not filter by type.
     * @param sender Sender of events to be listed, null indicates not filter by sender.
     * @param offset (Optional) The offset of events to start listing.
     * @return List of events in Notification Service.
     */
    protected abstract List<EventMeta> listEvents(
            String event_name, String namespace, String eventType, String sender, Long offset)
            throws Exception;

    /**
     * * Look up the offset of the first event whose create_time is bigger than the given timestamp
     *
     * @param timestamp The timestamp to look up.
     * @return The offset of the founded event.
     */
    protected abstract Long timeToOffset(Long timestamp) throws Exception;
}
