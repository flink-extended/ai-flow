import ai_flow as af
from ai_flow_plugins.job_plugins.bash import BashProcessor

# Initialize the project and workflow environment.
af.init_ai_flow_context()

# Define 2 bash jobs with simple commands.
with af.job_config('job_1'):
    af.user_define_operation(processor=BashProcessor("echo job_1"))
with af.job_config('job_2'):
    af.user_define_operation(processor=BashProcessor("echo job_2"))

# task_2 will be started after task_1 finished. Since we configured task_1 to runs periodically,
# the task_2 will also be triggered multiple times as long as task_1 finished.
af.action_on_job_status('job_2', 'job_1')
