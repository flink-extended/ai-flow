<!-- Licensed to the Apache Software Foundation (ASF) under one or more
contributor license agreements.  See the NOTICE file distributed with
this work for additional information regarding copyright ownership.
The ASF licenses this file to You under the Apache License, Version 2.0
(the "License"); you may not use this file except in compliance with
the License.  You may obtain a copy of the License at
  http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. -->

<template>
  <global-footer class="footer custom-render">
    <template v-slot:links>
      <a href="https://ai-flow.readthedocs.io" target="_blank">AIFlow</a>
      <a href="https://github.com/flink-extended/ai-flow" target="_blank">Github</a>
      <a href="https://github.com/flink-extended" target="_blank">@flink-extended</a>
    </template>
    <template v-slot:copyright>
      <div class="footer"><div class="copyright">&copy; AIFlow</div></div>
    </template>
  </global-footer>
</template>

<script>
import { GlobalFooter } from '@ant-design-vue/pro-layout'

export default {
  name: 'ProGlobalFooter',
  components: {
    GlobalFooter
  }
}
</script>
