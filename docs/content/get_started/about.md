# What's AIFlow

## Introduction
AIFlow is an event-driven workflow management framework that allows users to write machine learning pipelines that contain both stream and batch jobs. 

## Features
1. **Event-driven**: AIFlow schedule workflow and jobs based on events. This is more efficient than status-driven scheduling and be able to schedule the workflows that contain stream jobs.
2. **Extensible**: Users can easily define their own operators and executors to submit various types of tasks to different platforms.
3. **Exactly-once**: AIFlow provides an event processing mechanism with exactly-once semantics, which means that your tasks will never be missed or repeated even if a failover occurs.