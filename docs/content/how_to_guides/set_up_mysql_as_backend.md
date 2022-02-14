# Set up MySQL as Backend

Both [AIFlow](../deployment/deploying_aiflow_server.md) and [Notification Server](../deployment/deploying_notification_server.md) support MySQL as backend during deployment. By default, AIFlow and Notification Server use SQLite, which is intended for development purposes only. This document will show you how to set up MySQL as backend.

## Installing MySQL Client

To interacte with MySQL database, you need to install [mysqlclient](https://github.com/PyMySQL/mysqlclient) which is a MySQL database connector for Python. 

### Preparation

You need ensure that you have MySQL client libraries installed. You can check if you have installed locally by following command:

```shell
mysql_config --version
```

If you are getting `mysql_config: command not found` error, please following below commands to install MySQL client, otherwise you can skip this section.

#### macOS(Homebrew)

```shell
brew install mysql-client
echo 'export PATH="/usr/local/opt/mysql-client/bin:$PATH"' >> ~/.bash_profile
export PATH="/usr/local/opt/mysql-client/bin:$PATH"
```

#### Linux

```shell
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential # Debian / Ubuntu
sudo yum install python3-devel mysql-devel # Red Hat / CentOS
```

### Installing from PyPI

Now you can install mysqlclient with following command:

```shell
pip install 'ai-flow[mysql]'
```

## Initializing Database

You need to create a database and a database user that AIFlow will use to access this database. In the example below, a database `aiflow` and user with username `admin` with password `admin` will be created

```sql
CREATE DATABASE aiflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'admin' IDENTIFIED BY 'admin';
GRANT ALL PRIVILEGES ON aiflow.* TO 'admin';
```

```{note}
The database must use a UTF-8 character set
```

After initializing database, you can create tables for AIFlow or Notification Server with command-line.

#### AIFlow

```shell
aiflow db init
```

#### Notification Server

```shell
notification db init
```

## Configuration

Now you can modify the configurations about database connection to your mysql connection string of the following format

```shell
mysql+mysqldb://<user>:<password>@<host>[:<port>]/<dbname>
```

* For AIFLow you need to set `db_uri` to your mysql connection string and `db_type` to `MYSQL` in `aiflow_server.yaml`.
* For Notification Server you need to modify `db_uri` to your mysql connection string in `notification_server.yaml`.

