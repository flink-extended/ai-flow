import antdZhCN from 'ant-design-vue/es/locale-provider/zh_CN'
import momentZH from 'moment/locale/zh-cn'

import menu from './zh-CN/menu'
/*!
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

import setting from './zh-CN/setting'
import user from './zh-CN/user'
import project from './zh-CN/project'
import workflow from './zh-CN/workflow'
import job from './zh-CN/job'
import dataset from './zh-CN/dataset'
import model from './zh-CN/model'
import artifact from './zh-CN/artifact'

const components = {
  antLocale: antdZhCN,
  momentName: 'zh-cn',
  momentLocale: momentZH
}

export default {
  message: '-',

  'layouts.usermenu.dialog.title': '信息',
  'layouts.usermenu.dialog.content': '您确定要退出吗?',
  'layouts.userLayout.title': 'AIFlow是一个开源框架，将大数据和人工智能联系起来.',
  ...components,
  ...menu,
  ...setting,
  ...user,
  ...project,
  ...workflow,
  ...job,
  ...dataset,
  ...model,
  ...artifact
}
