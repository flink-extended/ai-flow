import ai_flow as af
from ai_flow_plugins.job_plugins.bash import BashProcessor

# Initialize the project and workflow environment.
af.init_ai_flow_context()

# Define 2 bash jobs with simple commands.
with af.job_config('job_1'):
    af.user_define_operation(processor=BashProcessor("echo job_1"))
with af.job_config('job_2'):
    af.user_define_operation(processor=BashProcessor("echo job_2"))

# Define relations between 2 jobs, job_2 would started after job_1 finished.
af.action_on_job_status(job_name='job_2', upstream_job_name='job_1')
