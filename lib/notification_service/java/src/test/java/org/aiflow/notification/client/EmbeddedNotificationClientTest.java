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

import org.aiflow.notification.entity.EventKey;
import org.aiflow.notification.entity.EventMeta;
import org.aiflow.notification.entity.SenderEventCount;
import org.aiflow.notification.service.PythonServer;
import org.apache.commons.lang3.tuple.ImmutablePair;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Properties;

import static org.aiflow.notification.conf.Configuration.CLIENT_ID_CONFIG_KEY;
import static org.aiflow.notification.conf.Configuration.CLIENT_INITIAL_SEQUENCE_NUMBER_CONFIG_KEY;
import static org.junit.Assert.assertEquals;

public class EmbeddedNotificationClientTest {

    private static EmbeddedNotificationClient client;
    private static PythonServer server;

    @Before
    public void setUp() throws Exception {
        server = new PythonServer();
        server.start();
        // waiting for notification server
        Thread.sleep(1000);
        // Create a NotificationClient using the in-process channel
        try {
            Properties properties = new Properties();
            client =
                    new EmbeddedNotificationClient(
                            "localhost:50051", "default", "sender", properties);
        } catch (Exception e) {
            throw new Exception("Failed to init notification client", e);
        }
    }

    @After
    public void tearDown() throws Exception {
        client.close();
        server.stop();
    }

    private static void prepareEvents(EmbeddedNotificationClient client) throws Exception {
        String namespace = "default";
        String sender = "sender";
        String eventType = "event_type";
        String message = "This is a message";
        String context = "{}";
        for (int i = 0; i < 3; i++) {
            client.sendEvent(
                    new EventMeta(
                            new EventKey("name" + i, eventType, namespace, sender),
                            message,
                            context));
        }
    }

    @Test
    public void testSendEvent() throws Exception {
        prepareEvents(client);
        List<EventMeta> eventList = this.client.listEvents(null, "default", null, null, 0l);
        assertEquals(3, eventList.size());
        assertEquals("name0", eventList.get(0).getEventKey().getName());
        assertEquals("name1", eventList.get(1).getEventKey().getName());
        assertEquals("name2", eventList.get(2).getEventKey().getName());
    }

    @Test
    public void testCountEvents() throws Exception {
        prepareEvents(client);
        client.sendEvent(
                new EventMeta(
                        new EventKey("name", "event_type", "default", "sender2"), "message", "{}"));
        assertEquals(
                1, this.client.countEvents("name0", "default", null, null, 0l).left.intValue());

        ImmutablePair<Long, List<SenderEventCount>> counts =
                this.client.countEvents(null, "default", "event_type", null, 0l);
        assertEquals(4, counts.left.intValue());
        assertEquals(3, counts.right.get(0).getEventCount());
        assertEquals(1, counts.right.get(1).getEventCount());

        assertEquals(
                2, this.client.countEvents(null, "default", null, "sender", 1l).left.intValue());
    }

    @Test
    public void testListEvents() throws Exception {
        prepareEvents(client);
        List<EventMeta> eventList = this.client.listEvents("name0", null, null, null, 0l);
        assertEquals(1, eventList.size());
        eventList = this.client.listEvents(null, "default", "event_type", null, 0l);
        assertEquals(3, eventList.size());
        eventList = this.client.listEvents(null, "default", null, "sender", null);
        assertEquals(3, eventList.size());
        eventList = this.client.listEvents(null, "default", null, "sender", 1l);
        assertEquals(2, eventList.size());
    }

    @Test
    public void testListAllEvents() throws Exception {
        prepareEvents(client);
        long startTime = 0;
        for (int i = 0; i < 3; i++) {
            EventMeta event =
                    this.client.sendEvent(
                            new EventMeta(
                                    new EventKey("name" + i, "type", "namespace", "sender"),
                                    "message",
                                    "{}"));
            if (i == 1) {
                startTime = event.getCreateTime();
            }
        }
        List<EventMeta> eventList = this.client.listAllEvents(0l, -1l, -1l);
        assertEquals(6, eventList.size());

        eventList = this.client.listAllEvents(startTime, -1l, -1l);
        assertEquals(2, eventList.size());

        eventList = this.client.listAllEvents(startTime, 3l, -1l);
        assertEquals(3, eventList.size());
    }

    @Test
    public void testListenEvent() throws Exception {
        final List<EventMeta> events = new ArrayList<>();
        ListenerRegistrationId handle = null;
        EventKey eventKey = new EventKey(null, "event_type", "namespace", "sender");
        try {
            handle =
                    client.registerListener(
                            new TestListenerProcessor(events),
                            Collections.singletonList(eventKey),
                            0l);
            for (int i = 0; i < 3; i++) {
                this.client.sendEvent(
                        new EventMeta(
                                new EventKey("name" + i, "event_type", "namespace", "sender"),
                                "message",
                                "{}"));
            }
        } finally {
            Thread.sleep(1000);
            client.unRegisterListener(handle);
        }
        assertEquals(3, events.size());
    }

    @Test
    public void testListenEventByName() throws Exception {
        final List<EventMeta> events = new ArrayList<>();
        ListenerRegistrationId handle = null;
        EventKey eventKey = new EventKey("name1", "event_type", "namespace", "sender");
        try {
            handle =
                    client.registerListener(
                            new TestListenerProcessor(events),
                            Collections.singletonList(eventKey),
                            0l);
            for (int i = 0; i < 3; i++) {
                this.client.sendEvent(
                        new EventMeta(
                                new EventKey("name" + i, "event_type", "namespace", "sender"),
                                "message",
                                "{}"));
            }
        } finally {
            Thread.sleep(1000);
            client.unRegisterListener(handle);
        }
        assertEquals(1, events.size());
        assertEquals("name1", events.get(0).getEventKey().getName());
    }

    @Test
    public void testListenEventBySender() throws Exception {
        final List<EventMeta> events = new ArrayList<>();
        ListenerRegistrationId handle = null;
        EventKey eventKey = new EventKey(null, null, null, "sender");
        try {
            handle =
                    client.registerListener(
                            new TestListenerProcessor(events),
                            Collections.singletonList(eventKey),
                            0l);
            for (int i = 0; i < 3; i++) {
                this.client.sendEvent(
                        new EventMeta(
                                new EventKey("name" + i, "event_type", "namespace", "sender"),
                                "message",
                                "{}"));
            }
        } finally {
            Thread.sleep(1000);
            client.unRegisterListener(handle);
        }
        assertEquals(3, events.size());
    }

    @Test
    public void testListenEventByType() throws Exception {
        final List<EventMeta> events = new ArrayList<>();
        ListenerRegistrationId handle = null;
        EventKey eventKey = new EventKey(null, "event_type", null, null);
        try {
            handle =
                    client.registerListener(
                            new TestListenerProcessor(events),
                            Collections.singletonList(eventKey),
                            0l);
            for (int i = 0; i < 3; i++) {
                this.client.sendEvent(
                        new EventMeta(
                                new EventKey("name" + i, "event_type", "namespace", "sender"),
                                "message",
                                "{}"));
            }
        } finally {
            Thread.sleep(1000);
            client.unRegisterListener(handle);
        }

        assertEquals(3, events.size());
    }

    @Test
    public void testGetLatestOffset() throws Exception {
        long latestVersion = this.client.getLatestOffset("default", "name");
        for (int i = 0; i < 3; i++) {
            this.client.sendEvent(
                    new EventMeta(
                            new EventKey("name", "event_type" + i, "default", "sender"),
                            "message",
                            "{}"));
        }
        long newLatestVersion = this.client.getLatestOffset("default", "name");
        assertEquals(latestVersion + 3, newLatestVersion);
    }

    @Test
    public void testTimeToOffset() throws Exception {
        long startTime = 0;
        for (int i = 0; i < 3; i++) {
            EventMeta event =
                    client.sendEvent(
                            new EventMeta(
                                    new EventKey("name" + i, "type", "namespace", "sender"),
                                    "message",
                                    "{}"));
            if (i == 1) {
                startTime = event.getCreateTime();
            }
        }
        assertEquals(2l, client.timeToOffset(startTime).longValue());
    }

    @Test
    public void testSendEventIdempotence() throws Exception {
        assertEquals(0, client.getSequenceNum().get());
        client.sendEvent(
                new EventMeta(
                        new EventKey("name", "event_type", "default", "sender"), "message1", "{}"));
        assertEquals(1, client.listEvents("name", "default", "event_type", "sender", 0l).size());
        assertEquals(1, client.getSequenceNum().get());

        client.sendEvent(
                new EventMeta(
                        new EventKey("name", "event_type", "default", "sender"), "message2", "{}"));
        assertEquals(2, client.listEvents("name", "default", "event_type", "sender", 0l).size());
        assertEquals(2, client.getSequenceNum().getAndDecrement());

        client.sendEvent(
                new EventMeta(
                        new EventKey("name", "event_type", "default", "sender"), "message3", "{}"));
        assertEquals(2, client.listEvents("name", "default", "event_type", "sender", 0l).size());
        assertEquals(2, client.getSequenceNum().get());
    }

    @Test
    public void testClientRecovery() throws Exception {
        Properties properties = new Properties();
        EmbeddedNotificationClient client1 =
                new EmbeddedNotificationClient("localhost:50051", "default", "sender", properties);

        assertEquals(0, client1.getSequenceNum().get());
        for (int i = 0; i < 3; i++) {
            client1.sendEvent(
                    new EventMeta(
                            new EventKey("name", "event_type", "default", "sender"),
                            "message" + i,
                            "{}"));
        }
        assertEquals(3, client1.listEvents("name", "default", "event_type", "sender", 0l).size());
        assertEquals(3, client1.getSequenceNum().get());

        properties.put(CLIENT_ID_CONFIG_KEY, client1.getClientId().toString());
        properties.put(CLIENT_INITIAL_SEQUENCE_NUMBER_CONFIG_KEY, "2");

        EmbeddedNotificationClient client2 =
                new EmbeddedNotificationClient("localhost:50051", "default", "sender", properties);

        try {
            client2.sendEvent(
                    new EventMeta(
                            new EventKey("name", "event_type", "default", "sender"),
                            "message3",
                            "{}"));
            List<EventMeta> events =
                    client2.listEvents("name", "default", "event_type", "sender", 0l);
            assertEquals(3, events.size());
            assertEquals("message2", events.get(2).getMessage());
            assertEquals(3, client2.getSequenceNum().get());

            client2.sendEvent(
                    new EventMeta(
                            new EventKey("name", "event_type", "default", "sender"),
                            "message4",
                            "{}"));
            events = client2.listEvents("name", "default", "event_type", "sender", 0l);
            assertEquals(4, events.size());
            assertEquals("message4", events.get(3).getMessage());
            assertEquals(4, client2.getSequenceNum().get());
        } finally {
            client2.close();
            client1.close();
        }
    }

    class TestListenerProcessor extends ListenerProcessor {
        public List<EventMeta> eventList;

        public TestListenerProcessor(List<EventMeta> events) {
            this.eventList = events;
        }

        @Override
        public void process(List<EventMeta> events) {
            this.eventList.addAll(events);
        }
    }
}
