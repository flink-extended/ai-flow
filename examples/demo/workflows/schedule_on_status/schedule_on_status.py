import ai_flow as af
from ai_flow.workflow.control_edge import JobAction
from ai_flow.workflow.status import Status
from ai_flow_plugins.job_plugins.bash import BashProcessor

# Initialize the project and workflow environment.
af.init_ai_flow_context()

# The workflow contains 3 jobs with simple bash commands.
with af.job_config('job_1'):
    af.user_define_operation(processor=BashProcessor("sleep 30"))
with af.job_config('job_2'):
    af.user_define_operation(processor=BashProcessor("sleep 60"))
with af.job_config('job_3'):
    af.user_define_operation(processor=BashProcessor("echo hello"))

# job_2 and job_3 will be started as soon as status of job_1 changed to RUNNING
af.action_on_job_status('job_2', 'job_1', upstream_job_status=Status.RUNNING, action=JobAction.START)
af.action_on_job_status('job_3', 'job_1', upstream_job_status=Status.RUNNING, action=JobAction.START)

# job_2 will be stopped as soon as job_1 finished
af.action_on_job_status('job_2', 'job_1', upstream_job_status=Status.FINISHED, action=JobAction.STOP)

# job_3 will be restarted as soon as job_2 is stopped completely
af.action_on_job_status('job_3', 'job_2', upstream_job_status=Status.KILLED, action=JobAction.RESTART)

