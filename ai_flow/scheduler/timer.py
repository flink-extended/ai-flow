# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from apscheduler.job import Job
from apscheduler.jobstores.base import BaseJobStore, JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.util import datetime_to_utc_timestamp, utc_timestamp_to_datetime
from notification_service.notification_client import NotificationClient

from ai_flow.metadata.timer import TimerMeta
from ai_flow.model.internal.events import PeriodicRunWorkflowEvent, PeriodicRunTaskEvent

try:
    import cPickle as pickle
except ImportError:  # pragma: nocover
    import pickle

try:
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.sql.expression import null
except ImportError:  # pragma: nocover
    raise ImportError('SQLAlchemyJobStore requires SQLAlchemy installed')


def send_start_workflow_event(client: NotificationClient, schedule_id):
    client.send_event(PeriodicRunWorkflowEvent(schedule_id=schedule_id))


def send_start_task_event(client: NotificationClient, workflow_execution_id, task_name):
    client.send_event(PeriodicRunTaskEvent(workflow_execution_id=workflow_execution_id,
                                           task_name=task_name))


def build_trigger(expression: str) -> BaseTrigger:
    index = expression.index('@')
    head = expression[: index]
    if 'cron' == head:
        cron_items = expression[index+1:].split(' ')
        if len(cron_items) == 8:
            time_zone = cron_items[7]
        else:
            time_zone = None
        return CronTrigger(second=cron_items[0],
                           minute=cron_items[1],
                           hour=cron_items[2],
                           day=cron_items[3],
                           month=cron_items[4],
                           day_of_week=cron_items[5],
                           year=cron_items[6],
                           timezone=time_zone)
    elif 'interval' == head:
        interval_items = expression[index + 1:].split(' ')
        if len(interval_items) != 4:
            raise ValueError('The interval expression {} is incorrect format, follow the pattern: '
                             'interval@days hours minutes seconds'.format(expression))
        temp_list = []
        for item in interval_items:
            if item is None or '' == item.strip():
                v = 0
            else:
                v = int(item.strip())
            if v < 0:
                raise Exception('The item of interval expression must be greater than or equal to 0.')

            temp_list.append(v)
        return IntervalTrigger(days=temp_list[0],
                               hours=temp_list[1],
                               minutes=temp_list[2],
                               seconds=temp_list[3]
                               )

    else:
        raise ValueError('The cron expression {} is incorrect format, follow the pattern: '
                         '1. Interval：interval@days hours minutes seconds '
                         '2. Cron：cron@second minute hour day month day_of_week year Optional(timezone).'
                         .format(expression))


class TimerJobStore(BaseJobStore):
    """ The class saves the scheduling information of periodic workflows/tasks to database."""
    def __init__(self, session, pickle_protocol=pickle.HIGHEST_PROTOCOL):
        super(TimerJobStore, self).__init__()
        self.pickle_protocol = pickle_protocol
        self.session = session

    def lookup_job(self, job_id):
        def _internal_lookup_job(job_id, session):
            job_state = session.query(TimerMeta.job_state).filter(TimerMeta.id == job_id).scalar()
            return self._reconstitute_job(job_state) if job_state else None

        job_state = _internal_lookup_job(job_id, self.session)
        return job_state

    def get_due_jobs(self, now):
        timestamp = datetime_to_utc_timestamp(now)
        return self._get_jobs(TimerMeta.next_run_time <= timestamp)

    def get_next_run_time(self):
        def _internal_get_next_run_time(session):
            next_run_time = session.query(TimerMeta.next_run_time).filter(
                TimerMeta.next_run_time != null()).order_by(TimerMeta.next_run_time).limit(1).scalar()
            return utc_timestamp_to_datetime(next_run_time)
        return _internal_get_next_run_time(self.session)

    def get_all_jobs(self):
        jobs = self._get_jobs()
        self._fix_paused_jobs_sorting(jobs)
        return jobs

    def add_job(self, job):
        """Uncommitted"""
        r = TimerMeta()
        r.id = job.id
        r.next_run_time = datetime_to_utc_timestamp(job.next_run_time)
        r.job_state = pickle.dumps(job.__getstate__(), self.pickle_protocol)
        self.session.add(r)

    def update_job(self, job):
        """Uncommitted"""
        def _internal_update_job(session):
            timer_meta = session.query(TimerMeta).filter(TimerMeta.id == job.id).first()
            if timer_meta is None:
                raise JobLookupError(job.id)
            else:
                timer_meta.next_run_time = datetime_to_utc_timestamp(job.next_run_time)
                timer_meta.job_state = pickle.dumps(job.__getstate__(), self.pickle_protocol)
                session.merge(timer_meta)
                session.commit()

        _internal_update_job(self.session)

    def remove_job(self, job_id):
        """Uncommitted"""
        self.session.query(TimerMeta).filter(TimerMeta.id == job_id).delete()

    def remove_all_jobs(self):
        self.session.query(TimerMeta).delete()
        self.session.commit()

    def _reconstitute_job(self, job_state):
        job_state = pickle.loads(job_state)
        job_state['jobstore'] = self
        job = Job.__new__(Job)
        job.__setstate__(job_state)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job

    def _get_jobs(self, *conditions):
        return self._internal_get_jobs(conditions, self.session)

    def _internal_get_jobs(self, conditions, session):
        jobs = []
        query = session.query(TimerMeta) \
            .order_by(TimerMeta.next_run_time)
        query = query.filter(*conditions) if conditions else query
        selectable_jobs = query.all()
        failed_job_ids = set()
        for job in selectable_jobs:
            try:
                jobs.append(self._reconstitute_job(job.job_state))
            except BaseException as e:
                self._logger.exception('Unable to restore job "%s exception [%s]" -- removing it', job.id, str(e))
                failed_job_ids.add(job.id)
        # Remove all the jobs we failed to restore
        if failed_job_ids:
            session.query(TimerMeta).filter(TimerMeta.id.in_(failed_job_ids)).delete()
            session.commit()
        return jobs


class Timer(object):
    def __init__(self, notification_client: NotificationClient, session):
        super().__init__()
        self.notification_client = notification_client
        self.store = TimerJobStore(session=session)
        jobstores = {
            'default': self.store
        }
        self.sc = BackgroundScheduler(jobstores=jobstores)

    def start(self):
        self.sc.start()

    def shutdown(self):
        self.sc.shutdown()

    @classmethod
    def generate_workflow_job_id(cls, schedule_id):
        return 'workflow:{}'.format(schedule_id)

    @classmethod
    def generate_task_job_id(cls, workflow_execution_id, task_name):
        return 'task:{}:{}'.format(workflow_execution_id, task_name)

    def add_workflow_schedule(self, schedule_id,  expression):
        self.sc.add_job(id=self.generate_workflow_job_id(schedule_id=schedule_id),
                        func=send_start_workflow_event, args=(self.notification_client, schedule_id),
                        trigger=build_trigger(expression=expression))

    def delete_workflow_schedule(self, schedule_id):
        job_id = self.generate_workflow_job_id(schedule_id=schedule_id)
        job = self.sc.get_job(job_id)
        if job is not None:
            self.sc.remove_job(job_id=job_id)

    def pause_workflow_schedule(self, schedule_id):
        job_id = self.generate_workflow_job_id(schedule_id=schedule_id)
        self.sc.pause_job(job_id)

    def resume_workflow_schedule(self, schedule_id):
        job_id = self.generate_workflow_job_id(schedule_id=schedule_id)
        self.sc.resume_job(job_id)

    def add_task_schedule(self, workflow_execution_id, task_name, expression):
        self.sc.add_job(id=self.generate_task_job_id(workflow_execution_id=workflow_execution_id, task_name=task_name),
                        func=send_start_task_event, args=(self.notification_client,
                                                          workflow_execution_id,
                                                          task_name),
                        trigger=build_trigger(expression=expression))

    def delete_task_schedule(self, workflow_execution_id, task_name):
        job_id = self.generate_task_job_id(workflow_execution_id=workflow_execution_id, task_name=task_name)
        job = self.sc.get_job(job_id)
        if job is not None:
            self.sc.remove_job(job_id=job_id)
