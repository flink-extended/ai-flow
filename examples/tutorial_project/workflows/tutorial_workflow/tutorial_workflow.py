#
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
#
import ai_flow as af
from ai_flow.model_center.entity.model_version_stage import ModelVersionEventType
from tutorial_processors import DatasetReader, ModelTrainer, ValidateDatasetReader, ModelValidator, Source, Sink, \
    Predictor

# Init project
af.init_ai_flow_context()

# Training of model
with af.job_config('train'):
    # Register metadata of training data(dataset) and read dataset(i.e. training dataset)
    train_dataset = af.get_dataset_by_name(dataset_name='tutorial_project.train_dataset')
    train_read_dataset = af.read_dataset(dataset_info=train_dataset,
                                         read_dataset_processor=DatasetReader())

    # Register model metadata and train model
    train_model = af.get_model_by_name(model_name="tutorial_project.KNN")
    train_channel = af.train(input=[train_read_dataset],
                             training_processor=ModelTrainer(),
                             model_info=train_model)

# Validation of model
with af.job_config('validate'):
    # Read validation dataset
    validate_dataset = af.get_dataset_by_name(dataset_name='tutorial_project.test_dataset')
    # Validate model before it is used to predict
    validate_read_dataset = af.read_dataset(dataset_info=validate_dataset,
                                            read_dataset_processor=ValidateDatasetReader())
    validate_artifact_name = 'tutorial_project.validate_artifact'
    validate_artifact = af.get_artifact_by_name(artifact_name=validate_artifact_name)
    validate_channel = af.model_validate(input=[validate_read_dataset],
                                         model_info=train_model,
                                         model_validation_processor=ModelValidator(validate_artifact_name))

# Prediction(Inference) using flink
with af.job_config('predict'):
    # Read test data and do prediction
    predict_dataset = af.get_dataset_by_name(dataset_name='tutorial_project.test_dataset')
    predict_read_dataset = af.read_dataset(dataset_info=predict_dataset,
                                           read_dataset_processor=Source())
    predict_channel = af.predict(input=[predict_read_dataset],
                                 model_info=train_model,
                                 prediction_processor=Predictor())
    # Save prediction result
    write_dataset = af.get_dataset_by_name(dataset_name='tutorial_project.write_dataset')
    af.write_dataset(input=predict_channel,
                     dataset_info=write_dataset,
                     write_dataset_processor=Sink())

# Define relation graph connected by control edge: train -> validate -> predict
af.action_on_model_version_event(job_name='validate',
                                 model_version_event_type=ModelVersionEventType.MODEL_GENERATED,
                                 model_name=train_model.name,
                                 namespace='tutorial_project')
af.action_on_model_version_event(job_name='predict',
                                 model_version_event_type=ModelVersionEventType.MODEL_VALIDATED,
                                 model_name=train_model.name,
                                 namespace='tutorial_project')
