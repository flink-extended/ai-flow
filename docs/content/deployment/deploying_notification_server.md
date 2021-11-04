# Deploying Notification Server

In this guide, we demonstrate how to deploy a Notification server.

## Starting Notification Server

In this section, we will show you how to use the default configuration to start an AIFlow server.

### Generate default configuration

To generate the default configuration of Notification server, you can run the following command:

```bash
init-notification-env.sh
```

This command will generate the [default configuration](default_config) file `notification_server.yaml` in
the `$NOTIFICATION_HOME` directory or `$HOME/notification_service` directory if `$NOTIFICATION_HOME` is not set.

```{note}
If the config file already exist, the script will not overwrite the config. If you intend to overwrite 
you existing config, you need to remove it manually and then run the script again.
```

You can refer to [here](configuration) if you want to learn all the configuration you can change.

### Start the Notification Server

You can start the Notification server with the following command.

```bash
start-notification.sh
```

It will start the notification server in a background process. You can check the log of the notification server
at `$NOTIFICATION_HOME/logs` directory. If you see "Notification server started." in the log, the notification service
is successfully started.

(configuration)=

## Configuration

This section shows an exhaustive list of available configuration of the Notification server.

### Notification Server

|Key|Type|Default|Description|
|---|---|---|---|
|server_port|Integer|50052|The port where the Notification server is exposed.|
|db_uri|String|sqlite:///{NOTIFICATION_HOME}/ns.db|The uri of the database backend for Notification server.|

(default_config)=

## Default Notification Server Configuration Example

```yaml
# port of notification server
server_port: 50052
# uri of database backend for notification server
db_uri: sqlite:///{NOTIFICATION_HOME}/ns.db
```