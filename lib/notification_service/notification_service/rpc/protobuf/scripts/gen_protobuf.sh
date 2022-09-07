#!/usr/bin/env bash
##
## Copyright 2022 The AI Flow Authors
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
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
root_dir=${current_dir}/..
proto_dir=${current_dir}/../proto

#generate python file
python3 -m grpc.tools.protoc -I${proto_dir} \
  -I/usr/local/include \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --python_out=${root_dir} \
  --grpc_python_out=${root_dir} \
  ${proto_dir}/notification_service.proto

#generate java file
protoc -I/usr/local/include -I${proto_dir} \
  -I$GOPATH/src -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --java_out=${root_dir}/../../../java/src/main/java \
  --proto_path=${root_dir}/proto \
  ${proto_dir}/notification_service.proto

protoc -I/usr/local/include -I${proto_dir} \
  -I$GOPATH/src -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --plugin=protoc-gen-grpc-java \
  --grpc-java_out=${root_dir}/../../../java/src/main/java \
  --proto_path=${root_dir}/proto \
  ${proto_dir}/notification_service.proto

#generate go file
protoc -I/usr/local/include -I${proto_dir} \
  -I$GOPATH/src \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --go_out=Mgoogle/api/annotations.proto=github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis/google/api,plugins=grpc:../go \
  ${proto_dir}/notification_service.proto

protoc -I/usr/local/include -I${proto_dir} \
  -I$GOPATH/src -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --grpc-gateway_out=logtostderr=true:../go \
  ${proto_dir}/notification_service.proto

cd ${current_dir}/..
sed -i -E 's/^import notification_service_pb2 as notification__service__pb2/from \. import notification_service_pb2 as notification__service__pb2/' *pb2*.py
rm -rf *.py-E
