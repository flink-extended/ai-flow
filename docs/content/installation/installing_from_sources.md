# Installing from Sources

This page describes installations from ai-flow source code.

## Prerequisites

Please make sure you have below tools installed on your workflow station.

* Git
* Python: 3.7, 3.8
* Pip: 19.0.0+
* SQLite: 3.15.0+

## Preparing Environment [Optional] 
To avoid dependencies conflict, we strongly recommend using [venv](https://docs.python.org/3.7/library/venv.html) or other similar tools for an isolated Python environment like below:

```shell
python3 -m venv venv_for_aiflow
source venv_for_aiflow/bin/activate
```

## Installing wheel
AIFlow would add some entrypoints to `PATH` during installation, which requires package `wheel` installed.
```shell script
python3 -m pip install wheel
``` 

## Downloading Source Code
```shell script
git clone https://github.com/flink-extended/ai-flow.git
```

## Installing AIFlow
Now you can install AIFlow by running:
```shell script
# cd into the source code directory you just cloned
cd ai-flow

# install notification service
python3 -m pip install lib/notification_service

# install ai-flow
python3 -m pip install .
```
