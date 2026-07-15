# ⭐️【Summary】Control Center Commands

_created: 20230831T102820Z / updated: 20240326T074441Z_

Systemctl (Uwsgi, Nginx, Celery, Redis)

⭐️ Systemctl Start/Stop/Restart  Shorthand

```
cd ~
. ./start.sh {servicename}
. ./stop.sh {servicename}
. ./restart.sh {servicename}
```

*chmod +x 
restart.sh

Start All Services

```
cd ~
. ./start.sh mongodb
. ./start.sh redis_session

. ./start.sh llm_redis
. ./start.sh llm_rabbitmq
. ./start.sh llm_server

. ./start.sh qdrant
. ./start.sh vectordb_redis_queue
. ./start.sh vectordb_celery

. ./start.sh uwsgi
. ./start.sh nginx
```

Status check shorthand

```
cd ~
. ./status.sh
```

Systemctl Commands

To start the services:

```
sudo systemctl start uwsgi
sudo systemctl start nginx
```

To stop the services:

```
sudo systemctl stop uwsgi
sudo systemctl stop nginx
```

To restart the services:

```
sudo systemctl restart uwsgi
sudo systemctl restart nginx
```

To enable the services to start on boot:

```
sudo systemctl enable uwsgi
sudo systemctl enable nginx
```

To disable the services from starting on boot:

```
sudo systemctl disable uwsgi
sudo systemctl disable nginx
```

To check the status of the services:

```
sudo systemctl status uwsgi
sudo systemctl status nginx
```

Sytemctl Inspection

起動中のサービスを調べる

```
systemctl list-units --type=service --all
systemctl list-units --type=service | grep redis
```

systemdで起動中のサービスの検索

```
$systemctl list-units --type=service | grep uwsgi
  uwsgi.service                                         loaded deactivating stop-sigterm       uWSGI Neuravoice Control Center
```

起動中のプロセスの検索

```
$ ps aux | grep uwsgi
kaz      2792056  0.0  0.0 553976 42356 pts/17   Ss+   8月31   0:03 journalctl -u uwsgi.service -f
kaz      2905084  0.0  0.0 137388 32112 ?        Sl   17:14   0:00 /src/neuravoice-control-center/venv/bin/uwsgi --ini /src/neuravoice-control-center/application/uwsgi/uwsgi.ini
kaz      2905111  0.0  0.0  19268  2592 pts/43   S+   17:14   0:00 grep --color=auto uwsgi
```

起動中の全サービスのエラーに関連するログ

```
$ journalctl -xe

 9月 01 17:16:04 supercom3 nginx[2905302]: 2023/09/01 17:16:04 [debug] 2905302#2905302: epoll timer: 0
 9月 01 17:16:04 supercom3 nginx[2905302]: 2023/09/01 17:16:04 [debug] 2905302#2905302: timer delta: 0
```

メモリ使用

```
$ free -h
               total        used        free      shared  buff/cache   available
Mem:           503Gi        15Gi       105Gi       143Mi       383Gi       485Gi
Swap:          2.0Gi       7.0Mi       2.0Gi
```

プロセス

```
sudo apt install htop
$ htop
```

GPUメモリを消費しているプロセス

```
nvidia-smi -l
| Processes:                                                                  |
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
|        ID   ID                                                   Usage      |
|=============================================================================|
|    0   N/A  N/A      1785      G   /usr/lib/xorg/Xorg                  4MiB |
|    0   N/A  N/A   1110080      C   ...center/venv/bin/python3.9    10438MiB |

$ ps -p 1110080 -o comm=
celery
```

Port

あるポートを使用しているプロセス

```
sudo lsof -i :6380
uwsgi     3788932  kaz   59u  IPv4 39493411      0t0  TCP localhost:47064->localhost:redis (CLOSE_WAIT)
redis-ser 3825606  kaz    6u  IPv6 39542342      0t0  TCP *:redis (LISTEN)
redis-ser 3825606  kaz    7u  IPv4 39542343      0t0  TCP *:redis (LISTEN)

sudo netstat -tuln | grep 6380
```

Sytemctl Log

redis

```
sudo journalctl -u redis-server.service
sudo journalctl  --output=cat -u redis-server.service
```

*-e : scroll to end

llm_service (long tail)

```
journalctl -u llm_server.service --no-pager | tail -n 3000
```

nginx

```
sudo journalctl --output=cat -u nginx.service -f
```

all

```
journalctl  # all services
journalctl -f -e  # scroll to end
```

Screen

起動中のscreenプロセス

```
$ screen -ls
There are screens on:
	585566.pts-187.supercom3	(2023年09月23日 13時09分00秒)	(Attached)
	584191.pts-182.supercom3	(2023年09月23日 13時08分43秒)	(Attached)
	583833.pts-180.supercom3	(2023年09月23日 13時08分37秒)	(Attached)
	583473.pts-175.supercom3	(2023年09月23日 13時08分31秒)	(Attached)
	583103.pts-158.supercom3	(2023年09月23日 13時08分24秒)	(Attached)
...
	1741078.pts-3.supercom3	(2023年08月07日 17時23分06秒)	(Detached)
	1740362.pts-3.supercom3	(2023年08月07日 17時12分22秒)	(Detached)
110 Sockets in /run/screen/S-kaz.
```

screenプロセスをkill

```
screen -r [session ID]
```

全てのscreen プロセスをkill

```
screen -ls | grep '(Detached)' | awk '{print $1}' | xargs -I {} screen -X -S {} quit
```

Nginx

Nginxの設定が問題ないか

```
$ sudo nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

Web App Frontend

⭐️ Build

Shorthand

```
cd ~
. ./watchsimplicity.sh  # run (1) below
. ./watchapp.sh  # run (2) below
```

build simplicity

```
cd application/views/src/ECMA/simplicity
gulp
```

(1) watch simplicity (if needed)

```
cd /src/neuravoice-control-center/application/views/src/ECMA/simplicity
sudo npx npm-run-all --parallel build:js compile:css
```

(2) Build sources. Copy simplicity. (and watch)

```
cd /src/neuravoice-control-center/application/views/
sudo npx npm-run-all --parallel compile:views:js compile:views:css copy:simplicity:js copy:simplicity:css
```

Install Prerequisite

```
git clone git@github.com:ThinkXInc/neuravoice-control-center.git
cd neuravoice-control-center
. ./venv/bin/activate
pip install -r requirements.txt
git submodule sync
git submodule update --init --recursive 
cd application/views
npm install
echo "127.0.0.1 service.localhost" | sudo tee -a /etc/hosts  # add host url
cd application/views/src/ECMA/simplicity
npm install
sudo apt install gulp
```

install node via nvm (avoiding permission problem)

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash
source ~/.bashrc
nvm install node
```

install gulp

```
npm install -g gulp-cli
```

LLM

Run LLM Prerequisites

```
pip install transformers accelerate
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Run LLM

celery

```
cd /src/neuravoice-control-center/application/server/llm
celery -A server:queue worker -l info
```

RabbitMQ

Console

```
http://180.57.171.75:8004/#/queues
```

guest

guest

Trouble Shooting

Error starting userland proxy: listen tcp4 
0.0.0.0:15672
: bind: address already in use"

```
$ sudo lsof -i :15672
```

COMMAND   PID     USER   FD   TYPE DEVICE SIZE/OFF NODE NAME beam.smp 1326 rabbitmq   33u  IPv4  54392      0t0  TCP *:15672 (LISTEN)

```
$ sudo systemctl stop rabbitmq-server
```

```
$ . ./start.sh llm_rabbitmq
```
