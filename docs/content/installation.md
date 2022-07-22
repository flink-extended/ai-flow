# Installation

This page describes installations using the `ai-flow` package [published in PyPI](https://pypi.org/project/ai-flow/).

## Prerequisites

AIFlow is tested with:

* Python: 3.7
* SQLite: 3.15.0+

**Note:** SQLite is only used in tests and getting started. To use AIFlow in production, please [set up MySQL as the backend](./how_to_guides/set_up_mysql_as_backend.md).

## Installing AIFlow

[Optional] To avoid dependencies conflict, we strongly recommend using [venv](https://docs.python.org/3.7/library/venv.html) or other similar tools for an isolated Python environment like below:

```shell
python3 -m venv venv_for_aiflow
source venv_for_aiflow/bin/activate
```

Now you can install AIFlow by running:

```shell script
python3 -m pip install ai-flow
```

Congrats, you are ready to run AIFlow and try core features following the [quickstart](./get_started/quickstart/locally.md).

## Extra Dependencies

The `ai-flow` PyPI basic package only installs what's needed to get started. Additional packages can be installed depending on what will be useful in your environment. For instance, when you are setting MySQL as the metadata backend, you need to install mysqlclient by following command:

```shell
python -m pip install 'ai-flow[mysql]'
```

For the list of the extras and what they enable, see: [Reference for package extras](../reference/extra_packages.md).