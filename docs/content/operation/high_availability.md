# High Availability
This guide provides an overview of High Availability feature of each component in AIFlow. 
Also it will show you how to configure and use them.

## Notification Service
AIFlow leverages Notification Service for message distribution among all processes so it's essential to keep it available. Notification Service is an embedded service in AIFlow Server by default for easier deployment, however, if you want to enable High Availability feature, 
it must be started as separate service.

### Start Notification Service Cluster
Suppose you choose MySQL as storage database and have 3 nodes to run Notification Service with HA enabled.

```text
# Run following commands on each node of your HA cluster
export DATABASE_CONN=mysql://username:password@database/table
start_notification_service.py --enable-ha=True --database-conn=${DATABASE_CONN} --port=50052
```
Now you can see ```Notification master started``` on each node and the cluster of Notification Service is ready.

### Configure AIFlow Server
By default the AIFlow contains an embedded Notification Service. In order to use the HA-cluster, you have to modify some configuration in ```aiflow_server.yaml``` and environment variables. Suppose you started Notification Service on node1, node2 and node3.
1. conf[start_default_notification]: Turn off the default embedded Notification Service.
```text
start_default_notification: False
```
2. conf[notification_server_uri]: Set the URIs of Notification servers you started with comma separated.
```text
notification_server_uri: node1:50052,node2:50052,node3:50052
```
3. env[NOTIFICATION_SERVER_URI]: Run following command before starting scheduler service to use HA-cluster. 
```
export NOTIFICATION_SERVER_URI='node1:50052,node2:50052,node3:50052'
```
4. conf[notification_server_uri] in section[scheduler_service]: It should be always identified with env[NOTIFICATION_SERVER_URI]
```
# scheduler config
scheduler_service:
  scheduler:
    scheduler_class: ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.AirFlowScheduler
    scheduler_config:
      airflow_deploy_path: ~/aiflow/airflow_deploy
      notification_server_uri: node1:50052,node2:50052,node3:50052
```

### Configure project.yaml
If you are connecting the HA Notification service in your project, all you need to do is adding below configuration to project.yaml.
```
notification_server_uri: node1:50052,node2:50052,node3:50052
```

