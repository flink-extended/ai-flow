# Extra Packages

Here's the list of all the extra dependencies of AIFlow.

## Database Extras

Those are extras that are needed when using specific database as backend.

| extra       | install command              | description                                     |
| ----------- | ---------------------------- | ----------------------------------------------- |
| mysql       | pip install 'ai-flow[mysql]' | MySQL as metadata backend                       |
| mongo       | pip install 'ai-flow[mongo]' | MongoDB as metadata backend                     |

## Blob Extras

Those are extras that are needed when using specific blob managers.

| extra       | install command              | description                                     |
| ----------- | ---------------------------- | ----------------------------------------------- |
| hdfs        | pip install 'ai-flow[hdfs]'  | HDFS as blob manager                            |
| oss         | pip install 'ai-flow[oss]'   | OSS as blob manager                             |
| s3          | pip install 'ai-flow[s3]'    | S3 as blob manager                              |

## Job Plugin Extras

Those are extras that add dependencies needed for integration with specific job plugins.

| extra       | install command              | description                                     |
| ----------- | ---------------------------- | ----------------------------------------------- |
| flink       | pip install 'ai-flow[flink]' | Flink job plugin                                |


## Scheduler Extras

Those are extras for scheduler(only apache-airflow for now).

| extra       | install command              | description                                     |
| ----------- | ---------------------------- | ----------------------------------------------- |
| celery      | pip install 'ai-flow[celery]'| Celery as the executor of apache-airflow        |

## Bundle Extras

Those are extras that install one ore more extras as a bundle.

| extra       | install command              | description                                     |
| ----------- | ---------------------------- | ----------------------------------------------- |
| example_requires | pip install 'ai-flow[example_requires]'| Should be installed when running provided AIFlow examples  |
| devel      | pip install 'ai-flow[devel]'| Minimum development dependencies, including flake8, pytest, coverage, etc.       |



