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
package org.aiflow.client.entity;

import org.aiflow.client.proto.Message;
import org.aiflow.client.proto.MetadataServiceOuterClass;

import java.util.ArrayList;
import java.util.List;

public class WorkflowSnapshotMeta {
    private Long uuid;
    private Long workflowId;
    private String uri;
    private String signature;
    private Long createTime;

    public WorkflowSnapshotMeta(
            Long uuid, Long workflowId, String uri, String signature, Long createTime) {
        this.uuid = uuid;
        this.workflowId = workflowId;
        this.uri = uri;
        this.signature = signature;
        this.createTime = createTime;
    }

    public Long getUuid() {
        return uuid;
    }

    public void setUuid(Long uuid) {
        this.uuid = uuid;
    }

    public Long getWorkflowId() {
        return workflowId;
    }

    public void setWorkflowId(Long workflowId) {
        this.workflowId = workflowId;
    }

    public String getUri() {
        return uri;
    }

    public void setUri(String uri) {
        this.uri = uri;
    }

    public String getSignature() {
        return signature;
    }

    public void setSignature(String signature) {
        this.signature = signature;
    }

    public Long getCreateTime() {
        return createTime;
    }

    public void setCreateTime(Long createTime) {
        this.createTime = createTime;
    }

    @Override
    public String toString() {
        return "WorkflowSnapshotMeta{"
                + "uuid="
                + uuid
                + ", workflowId="
                + workflowId
                + ", uri='"
                + uri
                + '\''
                + ", signature='"
                + signature
                + '\''
                + ", createTime="
                + createTime
                + '}';
    }

    public static WorkflowSnapshotMeta buildWorkflowSnapshotMeta(
            Message.WorkflowSnapshotProto workflowSnapshotProto) {
        return workflowSnapshotProto == null
                ? null
                : new WorkflowSnapshotMeta(
                        workflowSnapshotProto.getUuid(),
                        workflowSnapshotProto.getWorkflowId().getValue(),
                        workflowSnapshotProto.getUri().getValue(),
                        workflowSnapshotProto.getSignature().getValue(),
                        workflowSnapshotProto.getCreateTime().getValue());
    }

    public static List<WorkflowSnapshotMeta> buildWorkflowSnapshotMetas(
            MetadataServiceOuterClass.WorkflowSnapshotListProto workflowSnapshotListProto) {
        if (workflowSnapshotListProto == null) {
            return null;
        } else {
            List<WorkflowSnapshotMeta> workflowSnapshotMetas = new ArrayList<>();
            for (Message.WorkflowSnapshotProto proto :
                    workflowSnapshotListProto.getWorkflowSnapshotsList()) {
                workflowSnapshotMetas.add(buildWorkflowSnapshotMeta(proto));
            }
            return workflowSnapshotMetas;
        }
    }
}
