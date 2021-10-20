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

public class SenderEventCount {

    private String sender;
    private long eventCount;

    public SenderEventCount(String sender, long eventCount) {
        this.sender = sender;
        this.eventCount = eventCount;
    }

    public String getSender() {
        return sender;
    }

    public void setSender(String sender) {
        this.sender = sender;
    }

    public long getEventCount() {
        return eventCount;
    }

    public void setEventCount(long eventCount) {
        this.eventCount = eventCount;
    }

    @Override
    public String toString() {
        return "SenderEventCount{"
                + "sender='"
                + sender
                + '\''
                + ", eventCount="
                + eventCount
                + '}';
    }

    public static SenderEventCount buildSenderEventCount(
            NotificationServiceOuterClass.SenderEventCountProto eventCountProto) {
        return new SenderEventCount(eventCountProto.getSender(), eventCountProto.getEventCount());
    }
}
