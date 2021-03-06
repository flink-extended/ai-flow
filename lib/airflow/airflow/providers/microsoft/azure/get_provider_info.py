# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
def get_provider_info():
    return {
        'package-name': 'apache-airflow-providers-microsoft-azure',
        'name': 'Microsoft Azure',
        'description': '`Microsoft Azure <https://azure.microsoft.com/>`__\n',
        'versions': ['1.0.0'],
        'integrations': [
            {
                'integration-name': 'Microsoft Azure Batch',
                'external-doc-url': 'https://azure.microsoft.com/en-us/services/batch/',
                'tags': ['azure'],
            },
            {
                'integration-name': 'Microsoft Azure Blob Storage',
                'external-doc-url': 'https://azure.microsoft.com/en-us/services/storage/blobs/',
                'tags': ['azure'],
            },
            {
                'integration-name': 'Microsoft Azure Container Instances',
                'external-doc-url': 'https://azure.microsoft.com/en-us/services/container-instances/',
                'tags': ['azure'],
            },
            {
                'integration-name': 'Microsoft Azure Cosmos DB',
                'external-doc-url': 'https://azure.microsoft.com/en-us/services/cosmos-db/',
                'tags': ['azure'],
            },
            {
                'integration-name': 'Microsoft Azure Data Explorer',
                'external-doc-url': 'https://azure.microsoft.com/en-us/services/data-explorer/',
                'tags': ['azure'],
            },
            {
                'integration-name': 'Microsoft Azure Data Lake Storage',
                'external-doc-url': 'https://azure.microsoft.com/en-us/services/storage/data-lake-storage/',
                'tags': ['azure'],
            },
            {
                'integration-name': 'Microsoft Azure Files',
                'external-doc-url': 'https://azure.microsoft.com/en-us/services/storage/files/',
                'tags': ['azure'],
            },
            {
                'integration-name': 'Microsoft Azure FileShare',
                'external-doc-url': 'https://cloud.google.com/storage/',
                'tags': ['azure'],
            },
            {
                'integration-name': 'Microsoft Azure',
                'external-doc-url': 'https://azure.microsoft.com/',
                'tags': ['azure'],
            },
        ],
        'operators': [
            {
                'integration-name': 'Microsoft Azure Data Lake Storage',
                'python-modules': ['airflow.providers.microsoft.azure.operators.adls_list'],
            },
            {
                'integration-name': 'Microsoft Azure Data Explorer',
                'python-modules': ['airflow.providers.microsoft.azure.operators.adx'],
            },
            {
                'integration-name': 'Microsoft Azure Batch',
                'python-modules': ['airflow.providers.microsoft.azure.operators.azure_batch'],
            },
            {
                'integration-name': 'Microsoft Azure Container Instances',
                'python-modules': ['airflow.providers.microsoft.azure.operators.azure_container_instances'],
            },
            {
                'integration-name': 'Microsoft Azure Cosmos DB',
                'python-modules': ['airflow.providers.microsoft.azure.operators.azure_cosmos'],
            },
            {
                'integration-name': 'Microsoft Azure Blob Storage',
                'python-modules': ['airflow.providers.microsoft.azure.operators.wasb_delete_blob'],
            },
        ],
        'sensors': [
            {
                'integration-name': 'Microsoft Azure Cosmos DB',
                'python-modules': ['airflow.providers.microsoft.azure.sensors.azure_cosmos'],
            },
            {
                'integration-name': 'Microsoft Azure Blob Storage',
                'python-modules': ['airflow.providers.microsoft.azure.sensors.wasb'],
            },
        ],
        'hooks': [
            {
                'integration-name': 'Microsoft Azure Container Instances',
                'python-modules': [
                    'airflow.providers.microsoft.azure.hooks.azure_container_volume',
                    'airflow.providers.microsoft.azure.hooks.azure_container_registry',
                    'airflow.providers.microsoft.azure.hooks.azure_container_instance',
                ],
            },
            {
                'integration-name': 'Microsoft Azure Data Explorer',
                'python-modules': ['airflow.providers.microsoft.azure.hooks.adx'],
            },
            {
                'integration-name': 'Microsoft Azure FileShare',
                'python-modules': ['airflow.providers.microsoft.azure.hooks.azure_fileshare'],
            },
            {
                'integration-name': 'Microsoft Azure',
                'python-modules': ['airflow.providers.microsoft.azure.hooks.base_azure'],
            },
            {
                'integration-name': 'Microsoft Azure Batch',
                'python-modules': ['airflow.providers.microsoft.azure.hooks.azure_batch'],
            },
            {
                'integration-name': 'Microsoft Azure Data Lake Storage',
                'python-modules': ['airflow.providers.microsoft.azure.hooks.azure_data_lake'],
            },
            {
                'integration-name': 'Microsoft Azure Cosmos DB',
                'python-modules': ['airflow.providers.microsoft.azure.hooks.azure_cosmos'],
            },
            {
                'integration-name': 'Microsoft Azure Blob Storage',
                'python-modules': ['airflow.providers.microsoft.azure.hooks.wasb'],
            },
        ],
        'transfers': [
            {
                'source-integration-name': 'Local',
                'target-integration-name': 'Microsoft Azure Data Lake Storage',
                'how-to-guide': '/docs/apache-airflow-providers-microsoft-azure/operators/local_to_adls.rst',
                'python-module': 'airflow.providers.microsoft.azure.transfers.local_to_adls',
            },
            {
                'source-integration-name': 'Oracle',
                'target-integration-name': 'Microsoft Azure Data Lake Storage',
                'python-module': 'airflow.providers.microsoft.azure.transfers.oracle_to_azure_data_lake',
            },
            {
                'source-integration-name': 'Local',
                'target-integration-name': 'Microsoft Azure Blob Storage',
                'python-module': 'airflow.providers.microsoft.azure.transfers.file_to_wasb',
            },
            {
                'source-integration-name': 'Microsoft Azure Blob Storage',
                'target-integration-name': 'Google Cloud Storage (GCS)',
                'how-to-guide': '/docs/apache-airflow-providers-microsoft-azure/operators/azure_blob_to_gcs.rst',
                'python-module': 'airflow.providers.microsoft.azure.transfers.azure_blob_to_gcs',
            },
        ],
        'hook-class-names': [
            'airflow.providers.microsoft.azure.hooks.base_azure.AzureBaseHook',
            'airflow.providers.microsoft.azure.hooks.adx.AzureDataExplorerHook',
            'airflow.providers.microsoft.azure.hooks.azure_batch.AzureBatchHook',
            'airflow.providers.microsoft.azure.hooks.azure_cosmos.AzureCosmosDBHook',
            'airflow.providers.microsoft.azure.hooks.azure_data_lake.AzureDataLakeHook',
            'airflow.providers.microsoft.azure.hooks.azure_container_instance.AzureContainerInstanceHook',
            'airflow.providers.microsoft.azure.hooks.wasb.WasbHook',
        ],
    }
