# Deploying Notification Server

In this guide, we demonstrate how to deploy a Notification Server.

## Initialize Configuration

To initialize the default configuration file, you can run the following command:

```bash
notification config init
```

This command will generate the [default configuration](default_config) file `notification_server.yaml` in
the `$NOTIFICATION_HOME` directory(default is `$HOME/notification_service`).

```{note}
If the configration file already exists, the command will not generate the default configration. If you want to reset 
the configration, you need to remove it manually and then run the script again.
```

If you want to learn all configurations, you can refer to [here](configuration).

## Initialize Database

The database uri of Notification Server is configured in `notification_server.yaml`, you can run following command to initialize database.
```bash
notification db init
```

## Start the Notification Server

You can start the Notification Server with the following command in daemon mode.

```bash
notification server start -d
```

It will start the Notification Server in a background process. You can check the log of the Notification Server
at `$NOTIFICATION_HOME/logs` directory. `notification_server-*.log` is the log of Notification Server. If you see "
notification server started." in the log, the Notification Server successfully started.

(configuration)=

## Configuration

This section shows an exhaustive list of available configuration of the Notification Server.

### Notification Server

|Key|Type|Default|Description|
|---|---|---|---|
|server_port|Integer|50052|The port where the Notification Server is exposed.|
|db_uri|String|sqlite:///${NOTIFICATION_HOME}/ns.db|The uri of the database backend for Notification Server.|

(default_config)=

## Default Notification Server Configuration

```yaml
# port of notification server
server_port: 50052
# uri of database backend for notification server
db_uri: sqlite:///${NOTIFICATION_HOME}/ns.db
```

```{note}
The variable `${NOTIFICATION_HOME}` in above configuration should be replaced with your own path.
```
