/*
 * Copyright 2022 The AI Flow Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.aiflow.client.entity;

import org.aiflow.client.proto.Message.ModelVersionProto;

public class ModelVersionMeta {

    private int version;
    private String modelPath;
    private String modelType;
    private String versionDesc;
    private Long modelId;
    private Long projectSnapshotId;

    public ModelVersionMeta() {}

    public ModelVersionMeta(
            int version,
            String modelPath,
            String modelType,
            String versionDesc,
            Long modelId,
            Long projectSnapshotId) {
        this.version = version;
        this.modelPath = modelPath;
        this.modelType = modelType;
        this.versionDesc = versionDesc;
        this.modelId = modelId;
        this.projectSnapshotId = projectSnapshotId;
    }

    public int getVersion() {
        return version;
    }

    public void setVersion(int version) {
        this.version = version;
    }

    public String getModelPath() {
        return modelPath;
    }

    public void setModelPath(String modelPath) {
        this.modelPath = modelPath;
    }

    public String getModelType() {
        return modelType;
    }

    public void setModelType(String modelType) {
        this.modelType = modelType;
    }

    public String getVersionDesc() {
        return versionDesc;
    }

    public void setVersionDesc(String versionDesc) {
        this.versionDesc = versionDesc;
    }

    public Long getModelId() {
        return modelId;
    }

    public void setModelId(Long modelId) {
        this.modelId = modelId;
    }

    public Long getProjectSnapshotId() {
        return projectSnapshotId;
    }

    public void setProjectSnapshotId(Long projectSnapshotId) {
        this.projectSnapshotId = projectSnapshotId;
    }

    @Override
    public String toString() {
        return "ModelVersionMeta{"
                + "version='"
                + version
                + '\''
                + ", modelPath='"
                + modelPath
                + '\''
                + ", modelType='"
                + modelType
                + '\''
                + ", versionDesc='"
                + versionDesc
                + '\''
                + ", modelId="
                + modelId
                + ", projectSnapshotId="
                + projectSnapshotId
                + '}';
    }

    public static ModelVersionMeta buildModelVersionMeta(ModelVersionProto modelVersionProto) {
        return modelVersionProto == null
                ? null
                : new ModelVersionMeta(
                        modelVersionProto.getVersion().getValue(),
                        modelVersionProto.getModelPath().getValue(),
                        modelVersionProto.getModelType().getValue(),
                        modelVersionProto.getVersionDesc().getValue(),
                        modelVersionProto.getModelId().getValue(),
                        modelVersionProto.getProjectSnapshotId().getValue());
    }
}
