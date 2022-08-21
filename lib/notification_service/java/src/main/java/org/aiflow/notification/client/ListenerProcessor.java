package org.aiflow.notification.client;

import org.aiflow.notification.entity.EventMeta;

import java.util.List;

public abstract class ListenerProcessor {
    abstract void process(List<EventMeta> events);
}

