package org.aiflow.notification.entity;

public class EventKey {
    private String name;
    private String eventType;
    private String namespace;
    private String sender;

    public EventKey(String name, String eventType, String namespace, String sender) {
        this.name = name;
        this.eventType = eventType;
        this.namespace = namespace;
        this.sender = sender;
    }

    public String getName() {
        return name;
    }

    public String getEventType() {
        return eventType;
    }

    public String getNamespace() {
        return namespace;
    }

    public String getSender() {
        return sender;
    }

    @Override
    public String toString() {
        return "EventKey{"
                + "name='"
                + name
                + '\''
                + ", eventType='"
                + eventType
                + '\''
                + ", namespace='"
                + namespace
                + '\''
                + ", sender='"
                + sender
                + '\''
                + '}';
    }
}
