# Copyright 2022 The AI Flow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import json
from sqlalchemy import Column, String, Float, LargeBinary

from ai_flow.metadata.base import Base


class TimerMeta(Base):
    """
    It represents the metadata of the timer.
    """

    __tablename__ = "timer"

    id = Column(String(256), primary_key=True)
    next_run_time = Column(Float(25), nullable=True)
    job_state = Column(LargeBinary, nullable=True)
