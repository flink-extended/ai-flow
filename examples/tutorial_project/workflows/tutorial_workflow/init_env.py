# Copyright 2022 The AI Flow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import os
import ai_flow as af
from ai_flow.api.ai_flow_context import ensure_project_registered
from ai_flow.context.project_context import init_project_config

DATASET_URI = os.path.abspath(os.path.join(__file__, "../../../../")) + '/dataset_data/iris_{}.csv'
artifact_prefix = "tutorial_project."
project_path = os.path.abspath(os.path.join(__file__, "../../../"))
output_path = '/tmp/tutorial_output'


def init():
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # Register metadata of training data(dataset) and read dataset(i.e. training dataset)
    train_dataset = af.register_dataset(name=artifact_prefix + 'train_dataset',
                                        uri=DATASET_URI.format('train'))
    # Register test dataset
    validate_dataset = af.register_dataset(name=artifact_prefix + 'test_dataset',
                                           uri=DATASET_URI.format('test'))

    # Save prediction result
    write_dataset = af.register_dataset(name=artifact_prefix + 'write_dataset',
                                        uri=output_path + '/predict_result.csv')

    validate_artifact_name = artifact_prefix + 'validate_artifact'
    validate_artifact = af.register_artifact(name=validate_artifact_name,
                                             uri=output_path + '/validate_result')

    # Register model metadata and train model
    train_model = af.register_model(model_name=artifact_prefix + 'KNN',
                                    model_desc='KNN model')


if __name__ == '__main__':
    init_project_config(project_path + '/project.yaml')
    ensure_project_registered()
    init()
