

# aiflow task-execution run workflow_execution_id task_name seq_num --config
from ai_flow.model.status import TaskStatus

from ai_flow.model.task_execution import TaskExecution


def run_task_execution(args):
    with open("/Users/alibaba/Desktop/test_run_command", "w") as output_file:
        output_file.write(str(args))
