# Workflow Schedules

A Workflow Schedule is the periodic execution plan of the Workflow. 

## Creating Schedules

Users can add a Workflow Schedule to a Workflow by the following command.
```bash
aiflow workflow-schedule add workflow_name expression
```
The `expression` has two supported types: **cron** and **time interval**.

### Cron

Describes when to run the Workflow with a `Cron` expression which is in the format `cron@expression`. The `expression` is a standard crontab expression, see https://en.wikipedia.org/wiki/Cron for more information on the format accepted here.

The below command adds a Workflow Schedule to `my_workflow`, which makes the Workflow run at every hour.
```bash
aiflow workflow-schedule add my_workflow "cron@0 * * * *""
```

### Time Interval

Describes how often to run the Workflow from now on in the format `interval@days hours minutes seconds`, e.g. `interval0 0 10 0` means run the Workflow every 10 minutes from now on.

```bash
aiflow workflow-schedule add my_workflow "interval0 0 10 0"
```

## Viewing Schedules

Users can view all Schedules of the Workflow by the following command.
```bash
aiflow workflow-schedule list my_workflow
```

## Pausing and Resuming Schedules

If you want to temporarily stop a periodic schedule, you can run the following command.
```bash
aiflow workflow-schedule pause workflow_execution_id
```

Note that the above command doesn't delete the metadata of the Workflow Schedule, you can resume the periodic scheduling if needed.
```bash
aiflow workflow-schedule resume workflow_execution_id
```

## Deleting Schedules
To completely delete the metadata of the periodic scheduling, you can use the `delete` 
```bash
aiflow workflow-schedule delete workflow_execution_id
```