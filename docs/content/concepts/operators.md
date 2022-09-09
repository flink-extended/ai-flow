# Operators
An Operator is conceptually a template for a predefined [Task](./tasks.md), in other words, Task is an instantiated Operator.
AIFlow has an extensive set of operators available and some popular operators are built-in to the core:

* BashOperator - executes a bash command
* PythonOperator - calls an arbitrary Python function
* FlinkOperator - executes a `flink run` command to submit various Flink job
* SparkOperator - executes a `spark-submit` or `spark-sql` command to run various Spark job

## Operator Config
AIFlow Operators have some common configurations that can be passed as parameters when initializing the Operator.

### Periodic Task
Similar to Workflow, A Task can also run periodically by passing parameters `periodic_expression`. Instead of binding to a [Workflow Schedule](./workflow_schedules.md), A Task can only have one periodic expression which has the same format as the [Workflow Schedule](./workflow_schedules.md), e.g.

```python
from ai_flow.model.workflow import Workflow
from ai_flow.operators.bash import BashOperator

with Workflow(name='periodic_task_example') as workflow:
    task1 = BashOperator(name='task_1',
                         bash_command='echo I am the 1st task',
                         periodic_expression='cron@*/1 * * * *')
    task2 = BashOperator(name='task_2',
                         bash_command='echo I am the 2nd task',
                         periodic_expression='interval@0 0 1 0')
    task3 = BashOperator(name='task_3',
                         bash_command='echo I am the 3rd task')
    task3.start_after([task1, ])

```
```{note}
As AIFlow is event-based, tasks who start after a periodic task will also run periodically right after the upstream task finishes. In the above example, task3 will start running every time task1 finished.
```