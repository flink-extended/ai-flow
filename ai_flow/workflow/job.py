#
print
#
from typing import Text, List

from ai_flow.meta.dataset_meta import DatasetMeta

from ai_flow.graph.node import Node
from ai_flow.workflow.job_config import JobConfig


class Job(Node):
    """
    Job is a description of an executable unit,
    which contains information about the configuration and data required to run.
    """
    def __init__(self,
                 job_config: JobConfig) -> None:
        """
        :param job_config: Job configuration information(ai_flow.workflow.job_config.JobConfig).
        """
        super().__init__()
        self.job_config = job_config
        self.input_dataset_list: List[DatasetMeta] = []  # the job read dataset information
        self.output_dataset_list: List[DatasetMeta] = []  # the job write dataset information

    @property
    def job_name(self):
        """The name of the job."""
        return self.job_config.job_name
