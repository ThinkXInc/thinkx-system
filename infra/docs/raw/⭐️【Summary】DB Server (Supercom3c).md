# ⭐️【Summary】DB Server (Supercom3c)

_created: 20240530T011023Z / updated: 20241217T055915Z_

🌲【Summary】DB Summary

🌲Setup Supercom3c (DB server)

データセンターやること

【Disk増設】Supercom3c (DB) 1.5TB NVMe

IP: 192.168.1.9

DB Server で動かすもの

🍁 access table  6379

アクセス記録とアクセス可能リストの保持。

🍁 qdrant  6333

ベクターデータの保持。

🍁 redis for session 

セッションの保持。

🍁 mongodb 

ユーザー情報の保持

.env

.env (develop)

```
# Redis Session
REDIS_SESSION_HOST=localhost
REDIS_SESSION_PORT=6379
REDIS_SESSION_DB_NUMBER=1
REDIS_SESSION_LOGLEVEL=debug
REDIS_SESSION_EXPIRATION_TIME_SEC=90

# Redis AccessDB
REDIS_ACCESS_HOST=localhost
REDIS_ACCESS_PORT=6376
REDIS_ACCESS_DB_NUMBER=0

# MongoDB
MONGO_DB_URI=localhost
MONGO_PASS=pass

# VectorDB
VECTORDB_ENCODER_CHECKPOINT=sentence-transformers/all-MiniLM-L6-v2
VECTORDB_EMBEDDING_DIM=384
#VECTORDB_ENCODER_CHECKPOINT=sentence-transformers/all-mpnet-base-v2
#VECTORDB_EMBEDDING_DIM=768
VECTORDB_HOST=localhost
VECTORDB_PORT=6333
```

.env (

ディスク

NVMeポートに取り付けた1.5TB SSDを2つのパーティションに分割, /disk1に全dbのデータを保存 

(ディレクトリはdocker-compose.ymlに記載)

【Disk増設】Supercom3c (DB) 1.5TB NVMe

kaz@supercom3c:~$ df -h

,,,

/dev/nvme0n1p1 1007G   28K  956G   1% /disk1

/dev/nvme0n1p2  752G   28K  714G   1% /disk2

Docker

全てのdbをdocker-composeで管理する

🌲Setup Supercom3c (DB server)
 <- install docker, docker-compose

start all

```
cd /src/quantz-db
docker-compose up -d
```

stop all

```
cd /src/quantz-db
docker-compose down
```

log all

```
cd /src/quantz-db
docker-compose logs
```

qdrant (docker) log

```
sudo docker logs -f $(sudo docker ps -q --filter ancestor=qdrant/qdrant)
```

redis access table (docker) log

```
sudo docker logs -f $(sudo docker ps -q --filter name=quantz-db-redis-access-table-1)
```

redis session (docker) log

```
sudo docker logs -f $(sudo docker ps -q --filter name=quantz-db-redis-session-1)
```

mongodb (docker) log

```
sudo docker logs -f $(sudo docker ps -q --filter name=quantz-db-mongodb-1)
```

rabbitmq (docker) log

```
sudo docker logs -f $(sudo docker ps -q --filter name=quantz-db-rabbitmq-1)
```

MongoDB Client

From other servers

```
mongosh "mongodb://user:pass@192.168.1.9:27017/quantz"
```

*認証エラーの場合下記でログインしてユーザーを作成

```
mongosh "mongodb://user:pass@192.168.1.7:27017/quantz?authSource=admin"
use quantz
db.createUser({
  user: "user",
  pwd: "pass",
  roles: [{ role: "readWrite", db: "quantz" }]
});
```

```
use quantz
db.user.getIndexes()
```

flush

```
db.{collection}.drop()
```

Log in to docker

```
docker ps
sudo docker exec -it quantz-db-mongodb-1 /bin/bash
mongosh
use quantz
```

*下記のコマンドを外から叩いてもログインできない

```
mongosh "mongodb://user:pass@192.168.1.9:27017/quantz?authSource=admin"
```

Redis Client

```
redis-cli -h 192.168.1.9 -p 6376 -n 0
```

```
keys access_log::*
```

```
zrangebyscore access_log::ip::60.148.121.2 -inf +inf WITHSCORES
```

Backup System

⛰️【Summary】Backup DB System

Log

```
sudo tail -f /var/log/backup.log | ccze -A
```

Restart

```
sudo service cron restart
```

Status (if cron is active)

```
sudo service cron status
```

Run manually

```
sudo /src/quantz-db/backup_system/venv/bin/python backup.py
```

Edit crontab

```
sudo crontab -e
```

-> 記載内容など詳細は上のBackup DBノート参照

/src/quantz-db/backup_system/.env-setup

*restoreに必要

セキュリティ上使ったら削除しサーバーに残さない

```
AWS_ACCESS_KEY_ID=<REDACTED>
AWS_SECRET_ACCESS_KEY=<REDACTED>
AWS_REGION=ap-northeast-1
BACKUP_BUCKET_NAME=quantz-backup
FERNET_KEY=
```

* 24 12.17 supercom3cにアクセスできない状況でenv-setupを復元しようとしたがFERNET_KEYが見つからない

S3から手動でダウンロードしても復号しなければリストアできない

backup

```
cd /src/quantz-db/backup-system
python backup.py
```

-> FERNET_KEYで暗号化した状態でS3にPUTする

retrieve

```
cd /src/quantz-db/backup-system
python retreive.py
```

-> 復号化して./restore_dataに格納する

restore

```
cd /src/quantz-db/backup-system
python restore.py --db all
```

retrieve.pyを使って複合化された状態での./restore_data/*から各dbをリストアする

*未検証

よく使うコマンド

ポートの使用確認

```
sudo ss -tuln | grep 6333
```

```
sudo lsof -i :6333
```

```
sudo lsof -i :6333
sudo lsof -i :6380
sudo lsof -i :6376
sudo lsof -i :6379
sudo lsof -i :27017
```

動いているデーモンのサービス一覧

```
systemctl list-units --type=service
```

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

Restore Backup

S3からlatestデータをダウンロードする

*この方法では復号がさらに必要　そのままリストアできない
