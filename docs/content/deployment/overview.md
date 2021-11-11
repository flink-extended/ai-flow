# Overview

AIFlow is a platform that consists multiple components, AIFlow server, Notification server and Scheduler. The image
below shows the components of an AIFlow deployment.

AIFlow Server is the main component, which is responsible for submitting workflows to the scheduler, manage the life
cycle of the workflows, and bookkeeping the metadata of the AIFlow projects. Notification service is used to handle
event sending and event listening. The scheduler should support event-based scheduling and is responsible for scheduling
the workflow. All the components above need a database, and we use MySQL as the database. For more detail explanations of each
component, please refer to [Architecture Overview](../architecture/overview.md).

![Alt text](../images/AIFlow-Deploy-Overview.png)

## Installation

Please make sure you follow the [Installation Guide](./installation.md) to install AIFlow.

## Standalone Deployment

Here we show you how to set up an AIFlow Standalone Cluster.

```{note}
Since both AIFlow server, Airflow scheduler and Airflow web server are all depending on the Notification server,
Notification Server need to start first.
```

```{note}
Currently, AIFlow server and Airflow scheduler share a directory so that AIFlow server can submit Airflow dag file to 
Airflow scheduler. Therefore, it requires deploying AIFlow server and Airflow scheduler on the same machine.
```

### Deploying Notification Server

Notification server needs to start before other components. Please
follow [Deploying Notification Server](./deploying_notification_server.md) to start the notification server.

### Deploying AIFlow Server

Please follow [Deploying AIFlow Server](./deploying_aiflow_server.md) to start the AIFlow server.

### Deploying Scheduler

We use enhanced Airflow as our event-based scheduler. Please follow [Deploying Scheduler](./deploying_scheduler.md) to
start the Airflow scheduler.
