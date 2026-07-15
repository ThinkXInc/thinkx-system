# 🌲【Summary】DB Summary

_created: 20240327T033348Z / updated: 20241117T005008Z_

🌱 celery redis broker (web-server) 

```
redis://localhost:6380
```

🌱  llm rabbit mq 

llm推論のメッセンジャー。llm推論ごとに読み書きされ高速性が必要。redisと異なりリトライ可能で信頼性が高い。

* その後全てのCeleryプロセスのキューにこれが使われていることがわかった．Redisは結果の格納に使われている．割り当てを再考する．(TODO)

-> これがlocalにあると例えばあるサーバーで障害が起き別のサーバーであるユーザーの処理を実行する際にそのままでは決済スケジューラーの予約がない状態ではじまる

```
localhost:5672
user: guest
pass: :guest
```

🌱  core & general tasks rabbit mq 

core

transcribe, process_transcript, handle_llm_output, respond, 

general

llm_general_task, handle_llm_general_task_outputs

のタスクを全て処理するメッセンジャー．

これらのタスクはどれもwebsocket通信で処理されるため同一サーバーであることが保証される．

また失敗しても大きく支障がない．

-> アドレスは llm rabbit mq と共通

🌱 celery redis results llm

llm 推論時に一時的に結果を格納するのに使われる

llmサーバーと同じ端末に置き高速性を優先する

```
redis://localhost:6380
```

🌱 celery redis results processing (core & general) 

processingサーバーのCelery taskの結果格納用Redis

特にcore, general tasksの場合遅延がボトルネックにつながる

```
redis://localhost:6378
```

🌱 celery redis results vectordb 

vectordbサーバーのCelery taskの結果格納用Redis

```
redis://localhost:6380
```

🌱 redis for chat db

対話ログの格納。llm推論の度に更新される。特に高速性能が要求される。

```
/tmp/redis_chatdb.sock
```

🍁 access table  

アクセス記録とアクセス可能リストの保持。

```
redis://localhost:6376
```

🍁 web & vectordb rabbit mq

billingやreportプロセス用のメッセンジャーキュー

およびvector db用のメッセンジャーキュー

サーバーが停止してもキューが残り処理実行されなければならない．

DBサーバーが停止またはデータ消失-> バックアップまた復帰時に残タスクが処理される．そこで処理できなくてもリトライする．

メインサーバーが停止 -> 残タスクとしてペンディングされ復帰したら処理される．

-> キューが永続化されている限りいずれ処理されることが保証される．

```
192.168.1.9:5672
user: guest
pass: :guest
```

🍁 qdrant  

ベクターデータの保持。

```
usr/bin/docker run --name qdrant -p 6333:6333
```

🍁 redis for session 

セッションの保持。

```
192.168.1.9:6379
```

🍁 redis for chatdata

チャットログの保持。

```
192.168.1.9:6378
```

🍁 redis for interation_model

InteractionModelの保持。

```
192.168.1.9:6381
```

🍁 mongodb 

ユーザー情報の保持

```
192.168.1.9:27017
```

🌱: local

🍁: db server

DB Server Check 

```
ssh supercom3c
cd /src/quantz-db
docker-compose ps
```

NAME                                  COMMAND                  SERVICE                   STATUS                PORTS

quantz-db-mongodb-1                   "docker-entrypoint.s…"   mongodb                   running (unhealthy)   0.0.0.0:27017->27017/tcp, :::27017->27017/tcp

quantz-db-qdrant-1                    "./entrypoint.sh"        qdrant                    running               0.0.0.0:6333->6333/tcp, :::6333->6333/tcp, 6334/tcp

quantz-db-rabbitmq-1                  "docker-entrypoint.s…"   rabbitmq                  running               4369/tcp, 5671/tcp, 0.0.0.0:5672->5672/tcp, :::5672->5672/tcp, 15671/tcp, 15691-15692/tcp, 25672/tcp, 0.0.0.0:15672->15672/tcp, :::15672->15672/tcp

quantz-db-redis-access-table-1        "docker-entrypoint.s…"   redis-access-table        running               0.0.0.0:6376->6379/tcp, :::6376->6379/tcp

quantz-db-redis-chatdata-1            "docker-entrypoint.s…"   redis-chatdata            running               0.0.0.0:6378->6379/tcp, :::6378->6379/tcp

quantz-db-redis-interaction-model-1   "docker-entrypoint.s…"   redis-interaction-model   running               0.0.0.0:6381->6379/tcp, :::6381->6379/tcp

quantz-db-redis-session-1             "docker-entrypoint.s…"   redis-session             running               0.0.0.0:6379->6379/tcp, :::6379->6379/tcp

Timezone in container

```
docker ps
```

CONTAINER ID   IMAGE                 COMMAND                  CREATED        STATUS                    PORTS                                                                                                                                                 NAMES

25c9159a55ec   redis:latest          "docker-entrypoint.s…"   3 weeks ago    Up 3 weeks                0.0.0.0:6381->6379/tcp, :::6381->6379/tcp                                                                                                             quantz-db-redis-interaction-model-1

3c594590f9a9   redis:latest          "docker-entrypoint.s…"   5 months ago   Up 5 months               0.0.0.0:6378->6379/tcp, :::6378->6379/tcp                                                                                                             quantz-db-redis-chatdata-1

7c89b97ac86a   redis:latest          "docker-entrypoint.s…"   5 months ago   Up 5 months               0.0.0.0:6379->6379/tcp, :::6379->6379/tcp                                                                                                             quantz-db-redis-session-1

775e18dc2830   qdrant/qdrant         "./entrypoint.sh"        5 months ago   Up 5 months               0.0.0.0:6333->6333/tcp, :::6333->6333/tcp, 6334/tcp                                                                                                   quantz-db-qdrant-1

dcbdbc25e097   redis:latest          "docker-entrypoint.s…"   5 months ago   Up 5 months               0.0.0.0:6376->6379/tcp, :::6376->6379/tcp                                                                                                             quantz-db-redis-access-table-1

fb78f0eb7987   rabbitmq:management   "docker-entrypoint.s…"   5 months ago   Up 5 months               4369/tcp, 5671/tcp, 0.0.0.0:5672->5672/tcp, :::5672->5672/tcp, 15671/tcp, 15691-15692/tcp, 25672/tcp, 0.0.0.0:15672->15672/tcp, :::15672->15672/tcp   quantz-db-rabbitmq-1

a856959e135b   mongo:latest          "docker-entrypoint.s…"   5 months ago   Up 5 months (unhealthy)   0.0.0.0:27017->27017/tcp, :::27017->27017/tcp                                                                                                         quantz-db-mongodb-1

```
docker exec -it {container id} bash
```

root@fb78f0eb7987:/# 

```
date -u
```

Sun Nov 17 00:45:37 UTC 2024

Inspect

```
$ sudo ss -tuln | grep 6380
```

tcp   LISTEN 0      511          0.0.0.0:6380       0.0.0.0:*

tcp   LISTEN 0      511             [::]:6380          [::]:*

```
$ sudo lsof -i :6380
```

COMMAND    PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME

redis-ser 3211  kaz    6u  IPv6  88980      0t0  TCP *:6380 (LISTEN)

redis-ser 3211  kaz    7u  IPv4  88981      0t0  TCP *:6380 (LISTEN)

```
$ sudo ps -p 3211 -o lstart
```

                 STARTED

Wed May 24 19:25:28 2023

redis

```
redis-cli -h 192.168.1.9 -p 6378 ping
```

PONG

log

```
sudo journalctl -u redis-server.service
```

Service check

```
systemctl list-units --type=service | grep redis
```

Others

*MongoDBは手動で以下のセットアップが必要

```
docker exec -it quantz-db-mongodb-1 /bin/sh
mongosh
use admin
db.createUser({
    user: "admin",
    pwd: "adminpassword",
    roles: [{ role: "root", db: "admin" }]
});
exit
exit
docker-compose restart mongodb
docker exec -it quantz-db-mongodb-1 mongosh -u admin -p adminpassword --authenticationDatabase admin
use quantz
db.createUser({
    user: "user",
    pwd: "pass",
    roles: [{ role: "readWrite", db: "quantz" }]
});
docker exec -it quantz-db-mongodb-1 mongosh -u user -p pass --authenticationDatabase quantz
```

Check whether the mongodb setup works

```
$ docker exec -it quantz-db-mongodb-1 mongosh -u user -p pass --authenticationDatabase quantz
```

Current Mongosh Log ID:	665e7af729b29eed96a26a12

Connecting to:		mongodb://<credentials>@127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&authSource=quantz&appName=mongosh+2.2.6

Using MongoDB:		7.0.11

Using Mongosh:		2.2.6

For mongosh info see: https://docs.mongodb.com/mongodb-shell/

```
test> use quantz
```

switched to db quantz

```
quantz> db.user.findOne()
```

{

  _id: ObjectId('665c4c40deca414d4530d15a'),

  created: ISODate('2024-06-02T10:41:04.094Z'),

  updated: ISODate('2024-06-02T10:41:04.094Z'),

...

RabbitMQを個別に起動 

issue: rabbitmqコンテナが起動しない

```
docker run -d \
  --name quantz-db-rabbitmq-1 \
  -e RABBITMQ_DEFAULT_USER=guest \
  -e RABBITMQ_DEFAULT_PASS=guest \
  -p 5672:5672 \
  -p 15672:15672 \
  -v /disk1/rabbitmq/data:/var/lib/rabbitmq \
  -v /disk1/rabbitmq/log:/var/log/rabbitmq \
  rabbitmq:management
```
