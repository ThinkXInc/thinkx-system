# ⭐️ RabbitMQ

_created: 20231011T082854Z / updated: 20240421T084251Z_

web console

http://quantz.sixths.ai:8004/#/queues

command line monitoring

```
docker ps
docker exec -it {container id} bash
# rabbitmqctl list_queues
Timeout: 60.0 seconds ...
Listing queues for vhost / ...
name	messages
llm_queue	0
```

list queus in rabbitmq

```
rabbitmqctl list_queues
```

reset queue

```
rabbitmqctl purge_queue {queue name}
```

delayed message plugin in docker container

一時的にONにする

```
# enter the container
docker exec -it rabbitmq bash

# install plugin
apt-get update
apt-get install wget unzip -y
wget https://github.com/rabbitmq/rabbitmq-delayed-message-exchange/releases/download/v3.12.0/rabbitmq_delayed_message_exchange-3.12.0.ez
mv rabbitmq_delayed_message_exchange-3.12.0.ez /plugins/

# enable plugin
rabbitmq-plugins enable rabbitmq_delayed_message_exchange

# exit container
exit
```

永続化 (コンテナを作成)

```
vim application/rabbitmq/Dockerfile

---------------
FROM rabbitmq:3.12-management

RUN apt-get update && apt-get install wget unzip -y \
    && wget https://github.com/rabbitmq/rabbitmq-delayed-message-exchange/releases/download/v3.12.0/rabbitmq_delayed_message_exchange-3.12.0.ez \
    && mv rabbitmq_delayed_message_exchange-3.12.0.ez /plugins/ \
    && rabbitmq-plugins enable --offline rabbitmq_delayed_message_exchange
---------------

docker build -t custom-rabbitmq:latest .
```

Minotoring commands list

```

Monitoring, observability and health checks:

   activate_free_disk_space_monitoring    [Re-]activates free disk space monitoring on a node
   deactivate_free_disk_space_monitoring  Deactivates free disk space monitoring on a node
   list_bindings                          Lists all bindings on a vhost
   list_channels                          Lists all channels in the node
   list_ciphers                           Lists cipher suites supported by encoding commands
   list_connections                       Lists AMQP 0.9.1 connections for the node
   list_consumers                         Lists all consumers for a vhost
   list_exchanges                         Lists exchanges
   list_hashes                            Lists hash functions supported by encoding commands
   list_node_auth_attempt_stats           Lists authentication attempts on the target node
   list_queues                            Lists queues and their properties
   list_unresponsive_queues               Tests queues to respond within timeout. Lists those which did not respond
   ping                                   Checks that the node OS process is up, registered with EPMD and CLI tools can authenticate with it
   report                                 Generate a server status report containing a concatenation of all server status information for support purposes
   schema_info                            Lists schema database tables and their properties
   status                                 Displays status of a node
```

Clear (Purge) queue

```
$ docker ps
$ docker exec -it {image id} bash

# rabbitmqctl list_queues name messages_ready messages_unacknowledged

Timeout: 60.0 seconds ...
Listing queues for vhost / ...
name	messages_ready	messages_unacknowledged
celeryev.faff9e4b-6fca-49d6-861c-52dc346863aa	0	0
task_queue	0	0
celery@supercom3.celery.pidbox	0	0
celery	0	0
llm_queue	0	0

# rabbitmqctl purge_queue
```
