#!/usr/bin/env bash
##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
set -e

current_dir=$(cd "$(dirname "$0")";pwd)
root_dir=${current_dir}/../..
proto_dir=${current_dir}/../proto

#generate go file
protoc -I/usr/local/include -I${proto_dir} \
  -I$GOPATH/src \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --go_out=Mgoogle/api/annotations.proto=github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis/google/api,plugins=grpc:${current_dir}/../go \
  ${proto_dir}/message.proto

protoc -I/usr/local/include -I${proto_dir} \
  -I$GOPATH/src \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --go_out=Mgoogle/api/annotations.proto=github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis/google/api,plugins=grpc:${current_dir}/../go \
  ${proto_dir}/metadata_service.proto

protoc -I/usr/local/include -I${proto_dir} \
  -I$GOPATH/src -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --grpc-gateway_out=logtostderr=true:${current_dir}/../go \
  ${proto_dir}/metadata_service.proto

protoc -I/usr/local/include -I${proto_dir} \
  -I$GOPATH/src \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --go_out=Mgoogle/api/annotations.proto=github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis/google/api,plugins=grpc:${current_dir}/../go \
  ${proto_dir}/scheduler_service.proto

protoc -I/usr/local/include -I${proto_dir} \
  -I$GOPATH/src -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --grpc-gateway_out=logtostderr=true:${current_dir}/../go \
  ${proto_dir}/scheduler_service.proto


##generate java file
#protoc -I/usr/local/include -I${proto_dir} \
#  -I$GOPATH/src -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
#  --java_out=${root_dir}/java/client/src/main/java \
#  --proto_path=${current_dir} \
#  ${proto_dir}/message.proto
#
#protoc -I/usr/local/include -I${proto_dir} \
#  -I$GOPATH/src -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
#  --java_out=${root_dir}/java/client/src/main/java \
#  --proto_path=${current_dir} \
#  ${proto_dir}/metadata_service.proto
#
#protoc -I/usr/local/include -I${proto_dir} \
#  -I$GOPATH/src -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
#  --plugin=protoc-gen-grpc-java \
#  --grpc-java_out=${root_dir}/java/client/src/main/java \
#  --proto_path=${current_dir} \
#  ${proto_dir}/metadata_service.proto


#generate python file
python3 -m grpc.tools.protoc -I${proto_dir} \
  -I/usr/local/include \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --python_out=${current_dir}/.. \
  ${proto_dir}/message.proto

python3 -m grpc.tools.protoc -I${proto_dir} \
  -I/usr/local/include \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --python_out=${current_dir}/.. \
  --grpc_python_out=${current_dir}/.. \
  ${proto_dir}/metadata_service.proto

python3 -m grpc.tools.protoc -I${proto_dir} \
  -I/usr/local/include \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --python_out=${current_dir}/.. \
  --grpc_python_out=${current_dir}/.. \
  ${proto_dir}/heartbeat_service.proto

python3 -m grpc.tools.protoc -I${proto_dir} \
  -I/usr/local/include \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --python_out=${current_dir}/.. \
  --grpc_python_out=${current_dir}/.. \
  ${proto_dir}/scheduler_service.proto


cd ${current_dir}/..
sed -i -E 's/^import message_pb2 as message__pb2/from \. import message_pb2 as message__pb2/' *pb2*.py
sed -i -E 's/^import metadata_service_pb2 as metadata__service__pb2/from \. import metadata_service_pb2 as metadata__service__pb2/' *pb2*.py
sed -i -E 's/^import scheduler_service_pb2 as scheduler__service__pb2/from \. import scheduler_service_pb2 as scheduler__service__pb2/' *pb2*.py
sed -i -E 's/^import heartbeat_service_pb2 as heartbeat__service__pb2/from \. import heartbeat_service_pb2 as heartbeat__service__pb2/' *pb2*.py
rm -rf *.py-E
