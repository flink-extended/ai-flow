# Scheduler Plugin

By default, AIFlow server provides a modified version of AirFlow that supports event-based scheduling (EBS) to execute the workflows. Moreover, the scheduler also exposes the interface to manipulate the workflow and job executions. Although we are not aware of other schedulers capable of doing the same at this point, users can still create a custom scheduler for AIFlow if they want to.

## Implement a scheduler plugin

Compared with other plugins, implementation of the scheduler plugin might be a bit more involved. To create a scheduler plugin, one needs to implement a subclass of ``ai_flow.plugins_interface.scheduler_interface.Scheduler``. To take configurations upon construction, the subclass should have a `__init__(self, config: Dict)` method. The configurations for construction can be added to the AIFlow server configuration yaml file when one setup AIFlow server to use the custom scheduler. (see next section).

``ai_flow_plugins.scheduler_plugins.airflow_scheduler.AirFlowScheduler`` is a good example of the implementation of the scheduler plugin.

## Use a custom scheduler

To let AIFlow use a custom scheduler, one should set the ``scheduler.scheduler_class_name`` configuration in the server configuration yaml file, along with the configuration to construct the custom scheduler. The following example shows how to setup AIFlow server to use `AirFlowScheduler`.

```

    scheduler:
        scheduler_class_name: ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.AirFlowScheduler
        scheduler_config:
            airflow_deploy_path: /root/airflow/dag
            notification_server_uri: localhost:50052

```
