# Installation

This guide will show you how to install AIFlow.

## Prerequisites
1. python3.7
2. pip
3. MySQL Client

We strongly recommend using [virtualenv](https://virtualenv.pypa.io/en/latest/index.html) or other similar tools for an isolated Python environment in case of dependencies conflict error, e.g.


```shell
python3 -m venv /path/to/new/virtual/environment
source /path/to/new/virtual/environment/bin/activate
```

### Install MySQL Client
As AIFlow depends on [[mysqlclient|https://github.com/PyMySQL/mysqlclient]], you need ensure that you have MySQL client installed and `mysql_config` exists. You can check locally by following command:
```
mysql_config --version
```
If you are getting `mysql_config: command not found` error, please following below commands to install MySQL client, otherwise you can skip this section.

#### macOS (Homebrew)

```
brew install mysql-client
echo 'export PATH="/usr/local/opt/mysql-client/bin:$PATH"' >> ~/.bash_profile
export PATH="/usr/local/opt/mysql-client/bin:$PATH"
```

#### Linux
You can install MySQL development headers and libraries like so:

```
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential # Debian / Ubuntu
sudo yum install python3-devel mysql-devel # Red Hat / CentOS
```
Any problems please refer to [[mysqlclient installation|https://github.com/PyMySQL/mysqlclient#install]] for more information.

## Install AIFlow
### Install From PyPI

Installing AIFlow from PyPI is as simple as running the following command

```
pip install ai-flow
```

### Install From Source
To install AIFlow from source code, you need to have **yarn (1.22.10 or newer)** to compile the frontend of Airflow. Please refer to [Yarn Installation](https://classic.yarnpkg.com/en/docs/install) on how to install yarn. 

You could run the following commands at the root directory of the source code to install AIFlow:

```shell
cd flink-ai-extended
sh flink-ai-flow/bin/install_aiflow.sh
```
Note: depends on your local environment, you may occur `mysql_config not found` error if you did not install MySQL, 
please refer to the [Troubleshooting](#troubleshooting) section to solve it.

Some shell scripts like `start-all-aiflow-services.sh` will be installed with upon commands.
You could run with `which start-all-aiflow-services.sh` to check if the scripts are installed successfully. 

## Troubleshooting
### OSError: mysql_config not found
 If you are getting this error when installing AI Flow, you may have problems with mysqlclient installation. Please refer to mysqlclient's [document](https://github.com/PyMySQL/mysqlclient#install) to install mysqlclient properly.
