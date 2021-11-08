# Deploying Scheduler

In this guide, we demonstrate how to deploy a Scheduler. At present, the default Scheduler is the Airflow scheduler. The
deployment of the Airflow scheduler is as follows:

## Starting Airflow EventBased Scheduler

We use enhanced Airflow as an event-based scheduler and both
[LocalExecutor](https://airflow.apache.org/docs/apache-airflow/stable/executor/local.html) and
[CeleryExecutor](https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html) are supported. Follow below
steps to initialize configuration and start the Airflow scheduler.

### LocalExecutor

1. Prepare the default Airflow configuration. The following script will generate a default Airflow configuration
   file, `airflow.cfg` at the `$AIRFLOW_HOME` directory or `$HOME/airflow` directory if `$AIRFLOW_HOME` is not set.

   ```bash
   init-airflow-env.sh
   ```

   The script will also create an admin airflow user whose username and password are both `admin`. Please refer
   to [Configuration](configuration) and
   [Airflow Configuration Reference](https://airflow.apache.org/docs/apache-airflow/2.0.0/configurations-ref.html) for
   all the configuration you can change.

2. Start the Scheduler.

   ```bash
   start-airflow.sh
   ```

   You can check the log of the scheduler and Airflow webserver at `$AIRFLOW_HOME/logs` or `$HOME/airflow/logs`
   directory. `scheduler-*.log` is log of scheduler and `web-*.log` is log of Airflow web server. You can
   visit http://127.0.0.1:8080 to see the Airflow web server UI.

### CeleryExecutor

1. Prepare broker and backend. Celery needs a broker and a result backend to distribute and store tasks. For more
   information about setting up the broker and result backend, refer to the exhaustive
   [Celery documentation on the topic](https://docs.celeryproject.org/en/latest/getting-started/).

2. Set environment variables

   ```
   export AIRFLOW_HOME=~/airflow/home
   export MYSQL_CONN=mysql://username:password@database/table
   
   # You need to set the broker and result backend to the value you set up in step1. 
   # E.g. set both broker and result backend to redis://redis:6379/0.
   export BROKER_URL=redis://redis:6379/0
   export RESULT_BACKEND=redis://redis:6379/0
   ```

3. Prepare the Airflow configuration. To enable CeleryExecutor of the scheduler, you need to run the following command
   on scheduler server and all celery workers to make sure the configurations among hosts are equivalent. The broker URL
   and result backend you set up should be passed as well.

   ```bash
   init-airflow-with-celery-executor.sh $MYSQL_CONN $BROKER_URL $RESULT_BACKEND
   ```

4. Start Celery cluster.

   ```bash
   # Run following command on every Celery node in cluster, you may see ```celery@node_id ready.``` once worker started successfully.
   airflow celery worker
   ```

5. Start the Scheduler

   ```bash
   start-airflow.sh
   ```

(configuration)=

## Configuration

This section show a list of all the configurations we added to Airflow to make it works with AIFlow. Please refer to
[Airflow Configuration Reference](https://airflow.apache.org/docs/apache-airflow/2.0.0/configurations-ref.html) for all
other configurations.

|Section|Key|Type|Default|Description|
|---|---|---|---|---|
|webserver|notification_sql_alchemy_conn|String|sqlite:///${HOME}/notification_service/ns.db|The notification service db connection.|
|scheduler|notification_server_uri|String|127.0.0.1:50052|The notification server uri used by EventBasedSchedulerJob.|
