# Background
The flink workflow contains three flink jobs: process_flink_job, sql_flink_job and cluster_flink_job.

The process_flink_job runs as a single process using 
the ai_flow_plugins.job_plugins.flink.flink_processor.FlinkPythonProcessor api.

The sql_flink_job runs as a single process using 
the ai_flow_plugins.job_plugins.flink.flink_processor.FlinkSqlProcessor api.

The cluster_flink_job runs on the flink's local cluster using
the ai_flow_plugins.job_plugins.flink.flink_processor.FlinkPythonProcessor api.


# Check Flink Cluster Started
Before running the example, visit the [localhost:8081](localhost:8081) to check the flink environment.

Run the following command to start the flink cluster:
```shell
$FLINK_HOME/bin/start-cluster.sh
```

# Submit the Workflow
You can submit the workflow with the command:
```shell
aiflow workflow submit ${project_path} flink
```

# Run the Workflow
You can run the workflow with the command:
```shell
aiflow workflow start-execution ${project_path} flink
```

# Send Events to Run the Jobs
Since the jobs depend on event triggering, you need to send events to trigger jobs to run.

## Run the job named process_flink_job.
You can trigger the process_flink_job to run with the command:
```shell
notification event send run_job process_flink_job -s localhost:50052
```

## Run the job named sql_flink_job.
You can trigger the sql_flink_job to run with the command:
```shell
notification event send run_job sql_flink_job -s localhost:50052
```

## Run the job named cluster_flink_job.
You can trigger the cluster_flink_job to run with the command:
```shell
notification event send run_job cluster_flink_job -s localhost:50052
```

# Stop the Workflow Executions
You can stop all workflow executions with the command:
```shell
aiflow workflow stop-executions ${project_path} flink
```