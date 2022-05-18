from ai_flow.model.status import TaskStatus
from ai_flow.model.action import TaskAction
from ai_flow.model.workflow import Workflow
from ai_flow.model.operators.bash import BashOperator

with Workflow(name='workflow_1') as workflow_1:
    task_1 = BashOperator(name='task_1', bash_command='')
    task_2 = BashOperator(name='task_2', bash_command='')
    task_2.action_on_task_status(action=TaskAction.START,
                                 upstream_task_status_dict={task_1: TaskStatus.SUCCESS})


with Workflow(name='workflow_2') as workflow_2:
    task_1 = BashOperator(name='task_1', bash_command='')
    task_2 = BashOperator(name='task_2', bash_command='')
    task_2.action_on_task_status(action=TaskAction.START,
                                 upstream_task_status_dict={task_1: TaskStatus.SUCCESS})

string = 'A string'

obj = object()

workflow_3 = Workflow(name='workflow_3')

