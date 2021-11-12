# SDK Installation

This page describes the installation of the AIFlow SDK used for the workflow deployment. You should also check-out the `Prerequisites` that must be fulfilled when installing AIFlow SDK.

## Prerequisites

### Python 3.6 or 3.7

AIFlow SDK requires Python version 3.6 or 3.7, which version could be checked with the following command:

```shell script
python --version
```

Please make sure the Python version is 3.6.x or 3.7.x. If not, we strongly recommend using [virtualenv](https://virtualenv.pypa.io/en/latest/index.html) or other similar tools for an isolated Python environment in case of dependencies conflict error, e.g.

```shell
# install the Python 3.6 version
pip install virtualenv
virtualenv my_venv --python=python3.6
source my_venv/bin/activate

# install the Python 3.7 version
pip install virtualenv
virtualenv my_venv --python=python3.7
source my_venv/bin/activate
```

### MySQL Client

As the AIFlow SDK depends on the [mysqlclient](https://github.com/PyMySQL/mysqlclient), you need to ensure that you have installed the MySQL client and the `mysql_config` exists. You can check the installation of the MySQL client with the following command:

```
mysql_config --version
```

If you encounter an error that `mysql_config: command not found`, it's recommended to follow the below commands to install the MySQL client according to different system:

#### MacOS (Homebrew)

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

For any installation problems, please refer to the [mysqlclient installation](https://github.com/PyMySQL/mysqlclient#install) for more details.

## Install AIFlow SDK

Currently, AIFlow SDK only supports the PyPi installation.

```
pip install ai-flow-sdk
```
