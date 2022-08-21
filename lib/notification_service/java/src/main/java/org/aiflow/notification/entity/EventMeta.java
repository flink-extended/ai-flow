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
package org.aiflow.notification.entity;

import org.aiflow.notification.proto.NotificationServiceOuterClass;


public class EventMeta {

    private EventKey eventKey;
    private String message;
    private long offset;
    private long createTime;
    private String context;

    public EventMeta(EventKey eventKey, String message, String context) {
        this.eventKey = eventKey;
        this.message = message;
        this.context = context;
    }

    public EventKey getEventKey() {
        return eventKey;
    }

    public String getMessage() {
        return message;
    }

    public long getOffset() {
        return offset;
    }

    public long getCreateTime() {
        return createTime;
    }

    public String getContext() {
        return context;
    }

    public void setOffset(long offset) {
        this.offset = offset;
    }

    public void setCreateTime(long createTime) {
        this.createTime = createTime;
    }

    public void setContext(String context) {
        this.context = context;
    }

    @Override
    public String toString() {
        return "EventMeta{" +
                "eventKey=" + eventKey +
                ", message='" + message + '\'' +
                ", offset=" + offset +
                ", createTime=" + createTime +
                ", context='" + context + '\'' +
                '}';
    }

    public static EventMeta buildEventMeta(NotificationServiceOuterClass.EventProto eventProto) {
        EventKey eventKey = new EventKey(
                eventProto.getName(),
                eventProto.getEventType(),
                eventProto.getNamespace(),
                eventProto.getSender());
        EventMeta event = new EventMeta(
                eventKey,
                eventProto.getMessage(),
                eventProto.getContext());
        event.setOffset(eventProto.getOffset());
        event.setCreateTime(eventProto.getCreateTime());
        return event;
    }
}
