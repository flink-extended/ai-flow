import ai_flow as af
from ai_flow_plugins.job_plugins.bash import BashProcessor

# Initialize the project and workflow environment.
af.init_ai_flow_context()

# Define 5 bash jobs with simple commands.
with af.job_config('job_1'):
    af.user_define_operation(processor=BashProcessor("echo job_1"))
with af.job_config('job_2'):
    af.user_define_operation(processor=BashProcessor("echo job_2"))
with af.job_config('job_3'):
    af.user_define_operation(processor=BashProcessor("echo job_3"))
with af.job_config('job_4'):
    af.user_define_operation(processor=BashProcessor("echo job_4"))

# Workflow topology:#
#
# job_1 -> job_3
#
# job_2 -> job_4
#
# Since we configured job_1 and job_2 to runs periodically,
# the job_3 and job_4 will also be triggered multiple times as long as upstream jobs finished.

af.action_on_job_status(job_name='job_3', upstream_job_name='job_1')
af.action_on_job_status(job_name='job_4', upstream_job_name='2')



