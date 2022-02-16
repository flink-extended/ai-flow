# Installation

This page describes installations using the `ai-flow` package [published in PyPI](https://pypi.org/project/ai-flow/).

## Prerequisites

AIFlow is tested with:

* Python: 3.7
* Databases:
  * MySQL: 5.7, 8
  * SQLite: 3.15.0+

**Note:** SQLite is only used in developments and tests. To use AIFlow in production, please [set up MySQL as the backend](./how_to_guides/set_up_mysql_as_backend.md).

## Installing AIFlow

You can install AIFlow by running:

```shell script
python -m pip install ai-flow
```

To avoid dependencies conflict, we strongly recommend using [virtualenv](https://virtualenv.pypa.io/en/latest/index.html) or other similar tools for an isolated Python environment like below:

```shell
python -m pip install virtualenv
virtualenv venv_for_aiflow --python=python3.7
source venv_for_aiflow/bin/activate
```

## Extra Dependencies

The `ai-flow` PyPI basic package only installs what's needed to get started. Additional packages can be installed depending on what will be useful in your environment. For instance, when you are setting MySQL as the metadata backend, you need to install mysqlclient by following command

```shell
python -m pip install 'ai-flow[hdfs]' 
```

For the list of the extras and what they enable, see: [Reference for package extras](../reference/extra_packages.md).