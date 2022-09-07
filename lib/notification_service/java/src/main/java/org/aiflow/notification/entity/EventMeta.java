/*
 * Copyright 2022 The AI Flow Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
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

    private String key;
    private String value;

    private String namespace;
    private String sender;
    private long offset;
    private long createTime;
    private String context;

    public EventMeta(String key, String value) {
        this.key = key;
        this.value = value;
    }

    public String getKey() {
        return key;
    }

    public String getValue() {
        return value;
    }

    public String getNamespace() {
        return namespace;
    }

    public void setNamespace(String namespace) {
        this.namespace = namespace;
    }

    public String getSender() {
        return sender;
    }

    public void setSender(String sender) {
        this.sender = sender;
    }

    public long getOffset() {
        return offset;
    }

    public void setOffset(long offset) {
        this.offset = offset;
    }

    public long getCreateTime() {
        return createTime;
    }

    public void setCreateTime(long createTime) {
        this.createTime = createTime;
    }

    public String getContext() {
        return context;
    }

    public void setContext(String context) {
        this.context = context;
    }

    @Override
    public String toString() {
        return "EventMeta{"
                + "key='"
                + key
                + '\''
                + ", value='"
                + value
                + '\''
                + ", namespace='"
                + namespace
                + '\''
                + ", sender='"
                + sender
                + '\''
                + ", offset="
                + offset
                + ", createTime="
                + createTime
                + ", context='"
                + context
                + '\''
                + '}';
    }

    public static EventMeta buildEventMeta(NotificationServiceOuterClass.EventProto eventProto) {
        EventMeta event = new EventMeta(eventProto.getKey(), eventProto.getValue());
        event.setNamespace(eventProto.getNamespace());
        event.setSender(eventProto.getSender());
        event.setOffset(eventProto.getOffset());
        event.setContext(eventProto.getContext());
        event.setCreateTime(eventProto.getCreateTime());
        return event;
    }
}
