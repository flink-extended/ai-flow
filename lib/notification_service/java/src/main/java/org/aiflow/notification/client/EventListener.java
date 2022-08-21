/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
package org.aiflow.notification.client;

import com.google.common.util.concurrent.ThreadFactoryBuilder;
import org.aiflow.notification.entity.EventKey;
import org.aiflow.notification.entity.EventMeta;
import org.aiflow.notification.proto.NotificationServiceGrpc;
import org.apache.commons.collections4.CollectionUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.aiflow.notification.client.EmbeddedNotificationClient.listAllEvents;

public class EventListener {

    private static final Logger logger = LoggerFactory.getLogger(EventListener.class);
    private final NotificationServiceGrpc.NotificationServiceBlockingStub serviceStub;
    private final List<EventKey> eventKeys;
    private final long startOffset;
    private final long startTime;
    private final ListenerProcessor listernerProcessor;
    private final ExecutorService executorService;
    private final int timeoutSeconds;
    private volatile boolean isRunning = true;

    public EventListener(
            NotificationServiceGrpc.NotificationServiceBlockingStub serviceStub,
            List<EventKey> eventKeys,
            long startOffset,
            long startTime,
            ListenerProcessor listernerProcessor,
            Integer timeoutSeconds) {
        this.serviceStub = serviceStub;
        this.eventKeys = eventKeys;
        this.startOffset = startOffset;
        this.startTime = startTime;
        this.listernerProcessor = listernerProcessor;
        this.timeoutSeconds = timeoutSeconds;
        this.executorService =
                Executors.newSingleThreadExecutor(
                        new ThreadFactoryBuilder()
                                .setDaemon(true)
                                .setNameFormat("listen-notification-%d")
                                .build());
    }

    public void start() {
        this.executorService.submit(listenEvents());
    }

    public void shutdown() {
        this.isRunning = false;
        this.executorService.shutdown();
        try {
            this.executorService.awaitTermination(5000, TimeUnit.MILLISECONDS);
        } catch (InterruptedException ex) {
            logger.error("gRPC channel shutdown interrupted");
        }
    }

    private boolean match(EventKey eventKey, EventMeta event) {
        if (eventKey.getNamespace() != null
                && !eventKey.getNamespace().equals(event.getEventKey().getNamespace())) {
            return false;
        }
        if (eventKey.getName() != null
                && !eventKey.getName().equals(event.getEventKey().getName())) {
            return false;
        }
        if (eventKey.getEventType() != null
                && !eventKey.getEventType().equals(event.getEventKey().getEventType())) {
            return false;
        }
        if (eventKey.getSender() != null
                && !eventKey.getSender().equals(event.getEventKey().getSender())) {
            return false;
        }
        return true;
    }

    private List<EventMeta> filterEvents(List<EventKey> eventKeys, List<EventMeta> events) {
        if (eventKeys == null) {
            return events;
        }
        List<EventMeta> results = new ArrayList<>();
        for (EventMeta event : events) {
            for (EventKey key : eventKeys) {
                if (match(key, event)) {
                    results.add(event);
                    break;
                }
            }
        }
        return results;
    }

    public Runnable listenEvents() {
        return () -> {
            long listenOffset = this.startOffset;
            while (this.isRunning) {
                try {
                    if (Thread.currentThread().isInterrupted()) {
                        break;
                    }
                    List<EventMeta> events =
                            listAllEvents(
                                    this.serviceStub, -1l, listenOffset, -1l, this.timeoutSeconds);
                    if (events.size() > 0) {
                        events = filterEvents(eventKeys, events);
                    }
                    if (CollectionUtils.isNotEmpty(events)) {
                        this.listernerProcessor.process(events);
                        listenOffset = events.get(events.size() - 1).getOffset();
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                    throw new RuntimeException("Error while listening notification", e);
                }
            }
        };
    }
}
