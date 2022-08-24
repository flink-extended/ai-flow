# Installing from Sources

This page describes installations from ai-flow source code.

## Prerequisites

Please make sure you have below tools installed on your workflow station.

* Git
* Python: 3.7, 3.8
* Pip: 19.0.0+
* SQLite: 3.15.0+

## Downloading Source Code
```shell script
git clone https://github.com/flink-extended/ai-flow.git
```

## Installing

### Preparing Environment [Optional] 
To avoid dependencies conflict, we strongly recommend using [venv](https://docs.python.org/3.7/library/venv.html) or other similar tools for an isolated Python environment like below:

```shell
python3 -m venv venv_for_aiflow
source venv_for_aiflow/bin/activate
```

### Installing wheel
AIFlow would add some entrypoints to `PATH` during installation, which requires package `wheel` installed.
```shell script
pip install wheel
``` 

### Installing AIFlow
Now you can install AIFlow by running:
```shell script
# checkout active branch
cd ai-flow && git checkout dev

# install notification service
python3 -m pip install lib/notification_service

# install ai-flow
python3 -m pip install .
```
