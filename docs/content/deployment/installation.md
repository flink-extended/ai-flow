# Installation

This guide will show you how to install AIFlow.

## Prerequisites

### python3.7

AIFlow requires python3.7, you can check your version with following command:
```shell script
python --version
```
Please make sure the version is 3.7.x. 
We strongly recommend using [virtualenv](https://virtualenv.pypa.io/en/latest/index.html) or other similar tools for an isolated Python environment.

```shell
pip install virtualenv
virtualenv my_venv --python=python3.7
source my_venv/bin/activate
```

### MySQL Client
As AIFlow depends on [mysqlclient](https://github.com/PyMySQL/mysqlclient), you need ensure that you have MySQL client installed and `mysql_config` exists. You can check if you have installed locally by following command:
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

```
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential # Debian / Ubuntu
sudo yum install python3-devel mysql-devel # Red Hat / CentOS
```
Any problems please refer to [mysqlclient installation](https://github.com/PyMySQL/mysqlclient#install) for more information.

## Install AIFlow

Only pip installation is officially supported.

```
pip install ai-flow
```
It will take a few minutes to install dependencies for the first time.