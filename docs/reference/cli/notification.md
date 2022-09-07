# Notification

## Command Line Interface

Notification has a very rich command-line interface that supports many types of operations on Events, starting services and testing.

**Content**

* Positional Arguments
* Sub-commands:  

  * [server](notification-cli-server)
  * [event](notification-cli-event)
  * [config](notification-cli-config)
  * [db](notification-cli-db)
  * [version](notification-cli-version)

### notification

```
usage: notification [-h] COMMAND ... 
```

### Positional Arguments

> GROUP_OR_COMMAND

Possible choices: server, event, config, db, version.

### Sub-commands

(notification-cli-server)=

#### server

Notification server operations.

```
notification server [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: start, stop.

#### Sub-commands

##### start

Starts the notification server.

```
notification server start [-h] [-d]
```

##### Named Arguments

> -d, --daemon

Daemonizes instead of running in the foreground.

##### stop

Stops the notification server.

```
notification server stop [-h]
```

(notification-cli-event)=

#### event

Manages events.

```
notification event [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: count, list, listen, send.

#### Sub-commands

##### count

Counts events.

```
notification event count [-h] [--begin-offset BEGIN_OFFSET] [--begin-time BEGIN_TIME] [-n NAMESPACE] [--sender SENDER] [-s SERVER_URI] key
```

##### Positional Arguments

> key

Key of the event.

##### Named Arguments

> -s, --server-uri

The uri of notification server.

> -n, --namespace

Namespace of the event. If not set, all namespaces would be handled.

> --begin-offset

Begin offset of the event. Defaults to 0

> --begin-time

Begin datetime of the event, formatted in ISO 8601.

> --sender

Sender of the event.

##### list

Lists events.

```
notification event list [-h] [--begin-offset BEGIN_OFFSET] [--begin-time BEGIN_TIME] [-n NAMESPACE] [-o table, json, yaml] [--sender SENDER] [-s SERVER_URI] key
```

##### Positional Arguments

> key

Key of the event.

##### Named Arguments

> -s, --server-uri

The uri of notification server.

> -n, --namespace

Namespace of the event. If not set, all namespaces would be handled.

> --begin-offset

Begin offset of the event. Defaults to 0

> --begin-time

Begin datetime of the event, formatted in ISO 8601.

> --sender

Sender of the event.

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).   
Default: "table".

##### listen

Listens events

```
notification event listen [-h] [--begin-offset BEGIN_OFFSET] [--begin-time BEGIN_TIME] [-n NAMESPACE] [-s SERVER_URI] key
```

##### Positional Arguments

> key

Key of the event.

##### Named Arguments

> -s, --server-uri

The uri of notification server.

> -n, --namespace

Namespace of the event. If not set, all namespaces would be handled.

> --begin-offset

Begin offset of the event. Defaults to 0

> --begin-time

Begin datetime of the event to listen, formatted in ISO 8601.
Default: `datetime.now().isoformat()`.

##### send

Sends an event.

```
notification event send [-h] [--context CONTEXT] [-n NAMESPACE] [--sender SENDER] [-s SERVER_URI] key value
```

##### Positional Arguments

> key

Key of the event.

> value

Value of the event.

##### Named Arguments

> -s, --server-uri

The uri of notification server.

> -n, --namespace

Namespace of the event. If not set, all namespaces would be handled.

> --context

Context of the event.

> --sender

Sender of the event.

(notification-cli-config)=

#### config

Manages configuration.

```
notification config [-h] COMMAND ... 
```

#### Positional Arguments

> COMMAND

Possible choices: get-value, init, list.

#### Sub-commands

##### get-value

Gets the option value of the configuration.

```
notification config get-value [-h] option
```
 
##### Positional Arguments

> option

The option name of the configuration.

##### init

Initializes the default configuration.

```
notification config init [-h]
```

##### list

Lists all options of the configuration.

```
notification config list [-h] [--color {auto,off,on}]
```

##### Named Arguments

> --color

Possible choices: auto, off, on  
Do emit colored output (default: auto).  
Default: "auto".

(notification-cli-db)=

#### db

Database operations

```
notification db [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: downgrade, init, reset, upgrade.

##### Sub-commands

##### downgrade

Downgrades the metadata database to the version.

```
notification db downgrade [-h] [-v VERSION]
```

##### Named Arguments

> -v, --version

The version corresponding to the database.
Default: "heads".

##### init

Initializes the metadata database.

```
notification db init [-h]
```

##### reset

Burns down and rebuild the metadata database.

```
notification db reset [-h] [-y]
```

##### Named Arguments

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

##### upgrade

Upgrades the metadata database to the version

```
notification db upgrade [-h] [-v VERSION]
```

#### Named Arguments

> -v, --version

The version corresponding to the database.  
Default: "heads".

(notification-cli-version)=

#### version

Shows the version.

```
notification version [-h]
```
