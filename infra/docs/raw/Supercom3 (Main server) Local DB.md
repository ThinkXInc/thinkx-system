# Supercom3 (Main server) Local DB

_created: 20240708T065021Z / updated: 20241217T005926Z_

Rabbit MQ 5672
Redis LLM Results 6381
Redis VectorDB Results 6380
Redis Processing Results 6378
Redis ChatDB /tmp/redis_chatdb.sock (unix sock) 

🌲【Summary】DB Summary

run

```
cd /src/quantz/processing-server
docker-compose up -d
```

stop

```
cd /src/quantz/processing-server
docker-compose down
```

restart

```
cd /src/quantz/processing-server
docker-compose restart
```

log

```
cd /src/quantz/processing-server
docker-compose logs
```

Setup

data directory

```
sudo mkdir /var/lib/rabbitmq
sudo chown rabbitmq:rabbitmq /var/lib/rabbitmq

sudo mkdir /var/log/rabbitmq
sudo chown rabbitmq:rabbitmq /var/log/rabbitmq
```

```
sudo mkdir /var/log/redis_llm
sudo chown redis:redis /var/lib/redis_llm

sudo mkdir /var/log/redis_vectordb
sudo chown redis:redis /var/lib/redis_vectordb

sudo mkdir /var/log/redis_processing
sudo chown redis:redis /var/lib/redis_processing
```

.env

```
ln -s /src/quantz/.env /src/quantz/processing-server/.env
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

状態の確認

```
cd /src/quantz/processing-server
docker-compose ps
```

Name                                  Command               State                                     Ports

----------------------------------------------------------------------------------------------------------------------------------------------------------------

processing-server_rabbitmq_llm_1              docker-entrypoint.sh rabbi ...   Up      15671/tcp, 0.0.0.0:15672->15672/tcp,:::15672->15672/tcp, 15691/tcp,

                                                                                       15692/tcp, 25672/tcp, 4369/tcp, 5671/tcp,

                                                                                       0.0.0.0:5672->5672/tcp,:::5672->5672/tcp

processing-server_redis_llm_result_1          docker-entrypoint.sh redis ...   Up      0.0.0.0:6381->6379/tcp,:::6381->6379/tcp

processing-server_redis_processing_result_1   docker-entrypoint.sh redis ...   Up      0.0.0.0:6378->6379/tcp,:::6378->6379/tcp

processing-server_redis_vectordb_result_1     docker-entrypoint.sh redis ...   Up      
0.0.0.0:6380
->6379/tcp,:::6380->6379/tcp

```
sudo ss -tulnp | grep -E ':(5672|15672|6378|6380)'
```

check specific log

```
docker-compose logs redis_processing
```

Initialize Local Docker DBs

まずCeleryのautorestartプロセスを止めないとconnectionが作られてしまって止められない

Celeryを全部停止する

```
Restart=on-failure
```

->

```
#Restart=on-failure
```

コメントアウトし 

```
sudo systemctl daemon-reload
```

で設定ファイル更新

```
cd /src/quantz/processing-server/tasks_server/service
. ./stop.sh all
```

```
sudo systemctl stop llm_server.service
```

で全部停止

関連ファイルをバックアップし初期化

```
sudo mv /var/lib/rabbitmq /var/lib/rabbitmq.bk
sudo mv /var/lib/redis_processing /var/lib/redis_processing.bk
```

TODO:

drwxr-xr-x  2           999 root          4096 11月  3 13:47 redis_llm

drwxrwxr-x  2           999 redis         4096 11月  3 11:57 redis_llm.bak

drwxr-xr-x  2           999 redis         4096 11月  3 11:57 redis_llm_test

drwxr-xr-x  2           999 redis         4096 11月  3 13:47 redis_processing

drwxrwxr-x  2           999 redis         4096 11月  3 11:57 redis_processing.bak

drwxr-xr-x  2           999 root          4096 11月  3 13:47 redis_vectordb

drwxrwxr-x  2           999 redis         4096 11月  3 11:57 redis_vectordb.bak

同様に

dockerのコンテナを消して再起動

```
docker system prune -a --volumes
sudo systemctl restart docker
docker-compose up -d
```

だめなら下記の手順でdocker-composeをインストールし直す

解決したら再びCeleryプロセスを逆の手順で起動

dbがうまく動いていればエラーはでない

Restart All DBs

https://chatgpt.com/share/67270986-ca80-800d-ada1-5ea386f8d6a7

ディスクがいっぱいになるとdockerで起動しているlocal dbが不能になる

まずディスクを空ける
DBに接続している全てのCeleryプロセスを止める

llm_server.service

handle_llm_outputs.service

...

の

```
Restart=on-failure
```

->

```
#Restart=on-failure
```

コメントアウトし 

```
sudo systemctl daemon-reload
```

で設定ファイル更新

```
cd /src/quantz/processing-server/tasks_server/service
. ./stop.sh all
```

```
sudo systemctl stop llm_server.service
```

で全部停止

```
sudo ss -tulnp | grep -E ':(5672|15672|6378|6380)'
```

で全てのconnectionがkillされていることを確認

killされていなければ

```
kill -9 {process number}
```

でkill

```
cd /src/quantz/processing-server
```

dockerのコンテナを消す

```
docker system prune -a --volumes
```

dockerプロセスを再起動

```
sudo systemctl restart docker
```

```
docker-compose up -d
```

```
ERROR: for processing-server_redis_processing_result_1  Cannot start service redis_processing_result: error while creating mount source path '/var/lib/redis_processing': mkdir /var/lib/redis_processing: read-only file system
```

はreadonlyとみなされている

```
mount | grep "on / "
/dev/nvme0n1p2 on / type ext4 (rw,relatime,errors=remount-ro,stripe=32)
```

でrwと出たら/にマウントされたディスクは問題なく読み書きモード

```
ls -l /var/lib/
```

drwxr-xr-x  3           999 rabbitmq      4096 10月  4  2023 rabbitmq

drwxr-xr-x  2           999 redis         4096 11月  2 20:27 redis_llm

drwxr-xr-x  2           999 redis         4096 10月 23 07:40 redis_llm_test

drwxr-xr-x  2           999 redis         4096 11月  2 20:27 redis_processing

drwxr-xr-x  2           999 redis         4096 10月 23 08:47 redis_vectordb

もしこうでないなら

```
sudo chown -R 999:redis /var/lib/redis_llm /var/lib/redis_processing /var/lib/redis_vectordb
sudo chown -R 999:rabbitmq /var/lib/rabbitmq
```

で直す

999はdockerでrw権限なので問題ないはず

では何が原因? サーバーを再起動すべき?

もはやうつ手がないので

```
sudo reboot
```

解決しない

touch /var/lib/test
 
で書き込めることからディスクのマウントというよりdockerの問題のように見える

dockerを再インストールするのはどうか？

-> 

dockerを再インストールする

SnapバージョンのDockerは、そのコンテインメントモデルにより、より制限が厳しくなります。公式のDockerリポジトリからDockerをインストールすると、これらのコンテインメントの問題を回避した、より伝統的なインストールが可能です。

```
sudo snap remove docker
sudo rm -rf /var/lib/docker
sudo rm -rf /var/run/docker.sock
```

```
# Update the apt package index
sudo apt-get update

# Install packages to allow apt to use a repository over HTTPS
sudo apt-get install \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# Add Docker’s official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update the apt package index again
sudo apt-get update

# Install Docker Engine
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

```
sudo curl -L "https://github.com/docker/compose/releases/download/$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

```
docker-compose --version
```

```
sudo systemctl enable docker
sudo systemctl start docker
```

```
docker-compose up -d
```

Creating processing-server_redis_vectordb_result_1   ... done

Creating processing-server_redis_processing_result_1 ... done

Creating processing-server_redis_llm_result_1        ... done

Creating processing-server_rabbitmq_llm_1            ... done
