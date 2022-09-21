# AIFlow

[![CI](https://github.com/flink-extended/ai-flow/actions/workflows/flink_ai_flow_ci.yml/badge.svg)](https://github.com/flink-extended/ai-flow/actions/workflows/flink_ai_flow_ci.yml)
[![codecov](https://codecov.io/gh/flink-extended/ai-flow/branch/master/graph/badge.svg?token=ISWZNXUYO5)](https://codecov.io/gh/flink-extended/ai-flow)

## Introduction

AIFlow is an event-based workflow orchestration platform that allows users to
programmatically author and schedule workflows with a mixture of streaming and
batch tasks.

Most existing workflow orchestration platforms (e.g. Apache AirFlow, KubeFlow)
schedule task executions based on the status changes of upstream task
executions. While this approach works well for batch tasks that are guaranteed
to end, it does not work well for streaming tasks which might run for an
infinite amount of time without status changes. AIFlow is proposed to facilitate
the orchestration of workflows involving streaming tasks.

For example, users might want to run a Flink streaming job continuously to
assemable training data, and start a machine learning training job everytime the
Flink job has processed all upstream data for the past hour. In order to
schedule this workflow using non-event-based workflow orchestration platform,
users need to schedule the training job periodically based on wallclock time. If
there is traffic spike or upstream job failure, then the Flink job might not
have processed the expected amount of upstream data by the time the TensorFlow
job starts. The upstream job should either keep waiting, or fail fast, or
process partial data, none of which is ideal. In comparison, AIFlow provides
APIs for the Flink job to emit an event every time its event-based watermark
increments by an hour, which triggers the execution of user-specified training
job, without suffering the issues described above.

Learn more about AIFlow at https://ai-flow.readthedocs.io

## Features

1. Event-driven: AIFlow schedule workflow and jobs based on events. This is more efficient than status-driven scheduling and be able to schedule the workflows that contain stream jobs.

2. Extensible: Users can easily define their own operators and executors to submit various types of tasks to different platforms.

3. Exactly-once: AIFlow provides an event processing mechanism with exactly-once semantics, which means that your tasks will never be missed or repeated even if a failover occurs.

## Articles on AIFlow

- [B站基于AIFlow+Flink在批流融合调度上的实践](https://mp.weixin.qq.com/s/XC7BjfrbOrtFmumwhmctbA)


## Contributing

We happily welcome contributions to AIFlow in any ways, whether reporting problems, drafting features, or contributing code changes.
You can report problems to request features in the [GitHub Issues](https://github.com/flink-extended/ai-flow/issues).
If you want to contribute code changes, please check out the [contributing documentation](./CONTRIBUTING.md).


## Contact Us

For more information, we recommend you to join the **AIFlow Community Group** on the [Google Groups](https://groups.google.com) to contact us: **aiflow@googlegroups.com**.

You can also join the group on the [DingTalk](https://www.dingtalk.com). The number of the DingTalk group is `35876083`, which group can also be joined by scanning the QR code below:

![](https://raw.githubusercontent.com/wiki/alibaba/flink-ai-extended/images/dingtalk_qr_code.png)
