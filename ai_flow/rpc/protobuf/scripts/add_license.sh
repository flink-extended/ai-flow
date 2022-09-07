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
python_dir=${current_dir}/..
java_dir=${current_dir}/../java/client/src/main/java/org/aiflow/client/proto
go_dir=${current_dir}/../go/ai_flow
# Add licenses to generated python files
for i in ${python_dir}/*.py
do
   if ! [[ $i == *"__init__"* ]]; then
     sed -i '' -e '1i \
#\
# Copyright 2022 The AI Flow Authors\
#\
# Licensed under the Apache License, Version 2.0 (the "License");\
# you may not use this file except in compliance with the License.\
# You may obtain a copy of the License at\
#\
#   http://www.apache.org/licenses/LICENSE-2.0\
#\
# Unless required by applicable law or agreed to in writing,\
# software distributed under the License is distributed on an\
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY\
# KIND, either express or implied.  See the License for the\
# specific language governing permissions and limitations\
# under the License.\
#\
\
' $i
   fi

done


# Add licenses to generated go files
for i in ${go_dir}/*.gw.go
do
   sed -i '' -e '1i \
//\
// Copyright 2022 The AI Flow Authors\
//\
// Licensed under the Apache License, Version 2.0 (the "License");\
// you may not use this file except in compliance with the License.\
// You may obtain a copy of the License at\
//\
//     http://www.apache.org/licenses/LICENSE-2.0\
//\
// Unless required by applicable law or agreed to in writing, software\
// distributed under the License is distributed on an "AS IS" BASIS,\
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\
// See the License for the specific language governing permissions and\
// limitations under the License.\
\
' $i
done


