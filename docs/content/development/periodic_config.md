# Periodic Configuration

AIFlow supports periodic scheduling of workflows and jobs.

## Periodic Workflow Configuration
The following explains how to configure the workflow to run periodically.
We need to configure the **periodic_config** configuration item in the workflow configuration file.
The workflow periodic configuration supports two types: **cron expression** and **time interval**.

### 1. Cron Expression
The configuration below represents running the workflow every one minute with cron expression (**cron**) configuration item:
```yaml
periodic_config:
  cron: "0 */1 * * * * *"
  
job_1:
  job_type: bash
job_2:
  job_type: bash
```
The cron configuration item(* */1 * * * * *) means: **seconds minutes hours days months day_of_week years**.

### 2. Time Interval
The configuration below represents running the workflow every one minute with time interval (**interval**) configuration item:
```yaml
periodic_config:
  interval: "0,0,1,0"
  
job_1:
  job_type: bash
job_2:
  job_type: bash
```
The interval configuration item(0,0,1,0) means: **days,hours,minutes,seconds**.

## Periodic Job Configuration
The following explains how to configure the job to run periodically.
We need to configure the **periodic_config** configuration item under the job's configuration in the workflow configuration file.
The job periodic configuration supports two types: **cron expression** and **time interval**.

### 1. Cron Expression
The configuration below represents running the job named job_1 every one minute with cron expression (**cron**) configuration item:
```yaml
job_1:
  job_type: bash
  periodic_config:
    cron: "0 */1 * * * * *"
```
The cron configuration item(* */1 * * * * *) means: **seconds minutes hours days months day_of_week years**.

### 2. Time Interval
The configuration below represents running the job named job_2 every one minute with time interval (**interval**) configuration item:
```yaml
job_2:
  job_type: bash
  periodic_config:
    interval: "0,0,1,0"
```
The interval configuration item(0,0,1,0) means: **days,hours,minutes,seconds**.
