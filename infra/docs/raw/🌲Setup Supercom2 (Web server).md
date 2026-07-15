# 🌲Setup Supercom2 (Web server)

_created: 20240701T014705Z / updated: 20250313T111553Z_

essential packages

```
sudo apt update
sudo apt install curl
```

```
sudo apt-get install -y python3-dev python3-venv portaudio19-dev libffi-dev libssl-dev libsqlite3-dev wget screen vim nettools
```

bashrc

```
vim ~/.bashrc
```

```
# pip
alias pip=pip3

# git
alias push="git push origin master"
alias pull="git pull --rebase origin master"
alias add="git add ."
alias st="git status"

# mongodb
export PATH=/usr/local/bin/mongodb/bin:$PATH

# history
export HISTSIZE=10000
export HISTFILESIZE=10000
```

Git

supercom3: git

```
sudo apt install -y git
git config --global user.name "kazukiotsuka"
git config --global user.email otsuka.kazuki@googlemail.com
cd ~/.ssh
ssh-keygen -t ed25519 -C "otsuka.kazuki@googlemail.com"
Generating public/private ed25519 key pair.
Enter file in which to save the key (/root/.ssh/id_ed25519): id_github
Enter passphrase (empty for no passphrase):
Enter same passphrase again:

vim ~/.ssh/id_github.pub
# register this key to github

sudo apt-get update
sudo apt-get install keychain
(keychain --eval --agents ssh id_github)

vim ~/.ssh/config
Host github.com
   IdentityFile ~/.ssh/id_github
   Port 22

ssh -T git@github.com
```

alias

```
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage 'reset HEAD --'
```

lfs

```
sudo apt install git-lfs
```

Python

supercom3: Install Python3 on Linux (Ubuntu)

```
sudo apt update
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev
 libbz2-dev liblzma-dev
cd ~/Downloads
wget https://www.python.org/ftp/python/3.9.6/Python-3.9.6.tgz
tar -xf Python-3.9.6.tgz
cd Python-3.9.6/
./configure --enable-optimizations --with-ensurepip=upgrade --prefix=/usr/local
make -j 8  # replace "2" with the number of cores on your machine
sudo make altinstall
python3.9
```

* /usr/local/bin/にインストールされると/usr/bin/pythonがエラーを起こす(/usr/bin/上でimport しようとしてもないため) -> 
./configure --enable-optimizations --prefix=/usr
 -> この方法はシステムのpythonを上書きするのでよくない -> /usr/localを指定

No module named 'lsb_release'

*python3をpython3.9にリンクさせない 単に python3.9 -m venv venvでvenv内でpython3.9を使えばいい

Redis Cli

```
sudo apt install -y redis-tools
```

Autoenv

supercom3: autoenv

```
sudo apt install curl
curl -#fLo- 'https://raw.githubusercontent.com/hyperupcall/autoenv/master/scripts/install.sh' | sh
echo 'source ~/.autoenv/activate.sh' >> ~/.bashrc
echo 'export AUTOENV_ENV_FILENAME=.autoenv' >> ~/.bashrc
echo 'export AUTOENV_ENV_LEAVE_FILENAME=.autoenv_leave' >> ~/.bashrc
source ~/.bashrc
```

*permission denied が出たら 
curl -#fLo- 'https://raw.githubusercontent.com/hyperupcall/autoenv/master/scripts/install.sh' | sudo sh
 sudoをつけて実行する

*
~/.autoenv/
activate.shが作られなければ手動でこれを設置し
source ~/.bashrc

Install Docker

cf. 
Install docker to Ubuntu 22.04

uninstall old versions

```
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done
```

Update the 
apt
 package index and install packages to allow 
apt
 to use a repository over HTTPS:

```
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
```

Add Docker’s official GPG key:

```
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

 Use the following command to set up the repository:

```
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Update the 
apt
 package index:

```
sudo apt-get update
```

Install Docker Engine, containerd, and Docker Compose.

```
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify that the Docker Engine installation is successful by running the 
hello-world
 image.

```
sudo docker run hello-world
```

```
ls -l /var/run/docker.sock
sudo chown $USER /var/run/docker.sock
```

install docker-compose

```
 sudo curl -L "https://github.com/docker/compose/releases/download/v2.9.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

add $USER to docker group

```
sudo usermod -aG docker $USER
newgrp docker
```

Qdrant

```
docker pull qdrant/qdrant
```

*run qdrant server

```
docker run -p 6333:6333 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

MongoDB

```
sudo apt-get install gnupg curl
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
```

enable mongosh command

```
sudo apt-get install -y mongodb-org-shell
```

Create Admin User Group

```
sudo groupadd serveradmins
sudo usermod -a -G serveradmins kaz
```

Working Directory

```
sudo mkdir /src
sudo chown kaz:serveradmins /src
```

Clone Quantz DB Repository

```
cd /src
git clone git@github.com:ThinkXInc/quantz-web.git
```

Create venv and install pip manually

```
cd /src/quantz-web/web-server
python3.9 -m venv --without-pip venv
source venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
pip install --upgrade pip
```

Install Python dependencies

```
pip install -r requirements.txt
```

Update all submodules

```
cd /src/quantz-web
git submodule init
git submodule update --remote --recursive
```

Install node_modules

```
sudo apt install -y npm
```

```
cd /src/quantz-web
cd web-server/views/
npm install
```

watchappviews.sh
の

sudo npx npm-run-all --parallel compile:views:js compile:views:css copy:simplicity:js copy:simplicity:css

をsudoなしで実行できるようにする

```
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH="~/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

update npm

```
sudo npm install -g n
sudo n stable
sudo npm install -g npm
```

install globally

```
npm install -g @babel/cli less-watch-compiler npm-run-all
```

run

```
cd /src/quantz-web
cd web-server
cd views
npx npm-run-all --parallel compile:views:js compile:views:css copy:simplicity:js copy:simplicity:css
```

watchsimplicity.shが使えるようにする

```
cd /src/quantz-web/web-server
cd views/src/js/simplicity
npm install
```

run

```
cd /src/quantz-web/web-server/views
. ./watchsimplicity.sh
```

```
cd /src/quantz-web/web-server
cd views
. ./watchappviews.sh
```

web-clientでgulpができるようにする

```
sudo apt install -y gulp
npm install -g gulp-cli
```

```
cd /src/quantz-web/web-client
npm install
```

build simplicity

```
cd /src/quantz-web/
cd web-server/views/js/simplicity
npm install gulp
```

⠧

-> simplicity/node_modulesが全て揃うまで待つ 30分以上かかる

check global gulp

```
ls -l $(npm get prefix)/bin/gulp
$(npm get prefix)/bin/gulp --version
```

run

```
cd /src/quantz-web/web-client
gulp
```

*quantz-button.min.jsは現在gulpで自動で生成されないようにしている

以下のように最新のバージョンから生成する

```
cp /src/quantz-web/web-server/views/js/dist/quantz-button-v{version}.min.js /src/quantz-web/web-server/views/js/dist/quantz-button.min.js
```

vectordb_server

```
cd /src/quantz-web/vectordb_server
python3.9 -m venv --without-pip venv
. ./venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
pip install --upgrade pip
pip install -r requirements.txt
```

setup local db (rabbitmq, redis results)

quantz web-server setup develop environment in local

```
cd /src/quantz-web
vim .env
```

```
#ENV=production
ENV=develop

# App
FLASK_APP_SECRET_KEY = <REDACTED>
PASSWORD_ENCRYPT_KEY=<REDACTED>

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

## LLM

# RabbitMQ LLM 
RABBITMQ_LLM_USER=guest
RABBITMQ_LLM_HOST=localhost
RABBITMQ_LLM_PORT=5672
RABBITMQ_LLM_PASSWORD=<REDACTED>

# Redis Results LLM
REDIS_RESULTS_LLM_HOST=localhost
REDIS_RESULTS_LLM_PORT=6380
REDIS_RESULTS_LLM_LOGLEVEL=debug
REDIS_RESULTS_LLM_DB_NUMBER=0
REDIS_RESULTS_LLM_EXPIRATION_TIME_SEC=180
#REDIS_RESULTS_LLM_PASSWORD=<REDACTED>

# Processing (Core, General)

# RabbitMQ Processing
RABBITMQ_PROCESSING_USER=guest
RABBITMQ_PROCESSING_HOST=localhost
RABBITMQ_PROCESSING_PORT=5672
RABBITMQ_PROCESSING_PASSWORD=<REDACTED>

# Redis Results Processing
REDIS_RESULTS_PROCESSING_HOST=localhost
REDIS_RESULTS_PROCESSING_PORT=6378
REDIS_RESULTS_PROCESSING_LOGLEVEL=debug
REDIS_RESULTS_PROCESSING_DB_NUMBER=0
REDIS_RESULTS_PROCESSING_EXPIRATION_TIME_SEC=180

# Redis Local ChatDB
REDIS_LOCAL_CHATDB_ADDRESS=/tmp/redis_chatdb.sock

# Redis Chatdata
REDIS_CHATDATA_HOST=localhost
REDIS_CHATDATA_PORT=6378
REDIS_CHATDATA_DB_NUMBER=0
REDIS_CHATDATA_LOGLEVEL=debug
REDIS_CHATDATA_EXPIRATION_TIME_SEC=604800
REDIS_CHATDATA_QUEUE_NAME=chatdata_queue

## VectorDB

VECTORDB_ENCODER_CHECKPOINT=sentence-transformers/all-MiniLM-L6-v2
VECTORDB_EMBEDDING_DIM=384
#VECTORDB_ENCODER_CHECKPOINT=sentence-transformers/all-mpnet-base-v2
#VECTORDB_EMBEDDING_DIM=768
VECTORDB_HOST=localhost
VECTORDB_PORT=6333

# RabbitMQ VectorDB
RABBITMQ_VECTORDB_USER=guest
RABBITMQ_VECTORDB_HOST=localhost
RABBITMQ_VECTORDB_PORT=5672
RABBITMQ_VECTORDB_PASSWORD=<REDACTED>

# Redis Results VectorDB
REDIS_RESULTS_VECTORDB_HOST=localhost
REDIS_RESULTS_VECTORDB_PORT=6380
REDIS_RESULTS_VECTORDB_LOGLEVEL=debug
REDIS_RESULTS_VECTORDB_DB_NUMBER=0
REDIS_RESULTS_VECTORDB_EXPIRATION_TIME_SEC=180

## Web (Billing Scheduler, Report etc.)

# RabbitMQ Web
RABBITMQ_WEB_USER=guest
RABBITMQ_WEB_HOST=localhost
RABBITMQ_WEB_PORT=5672
RABBITMQ_WEB_PASSWORD=<REDACTED>

# Redis Results Web
REDIS_RESULTS_WEB_HOST=localhost
REDIS_RESULTS_WEB_PORT=6380
REDIS_RESULTS_WEB_LOGLEVEL=debug
REDIS_RESULTS_WEB_DB_NUMBER=0
REDIS_RESULTS_WEB_EXPIRATION_TIME_SEC=180

# AWS
AWS_ACCESS_KEY_ID=<REDACTED>
AWS_SECRET_ACCESS_KEY=<REDACTED>
AWS_DEFAULT_REGION=ap-northeast-1

# Stripe
STRIPE_SECRET_KEY=<REDACTED>
```

docker compose (vectordb)

```
cd /src/quantz-web
ln -s .env vectordb_server/.env  # docker-compose can recognize only the same or under the directory
```

```
sudo chmod +x /usr/local/bin/docker-compose
cd /src/quantz-web/vectordb_server
docker-compose up -d
```

```
cd /src/quantz-web/vectordb_server/
docker-compose ps
NAME                         COMMAND                  SERVICE             STATUS              PORTS
vectordb_server-rabbitmq-1   "docker-entrypoint.s…"   rabbitmq            running             4369/tcp, 5671/tcp, 0.0.0.0:5672->5672/tcp, :::5672->5672/tcp, 15671/tcp, 15691-15692/tcp, 25672/tcp, 0.0.0.0:15672->15672/tcp, :::15672->15672/tcp
vectordb_server-redis-1      "docker-entrypoint.s…"   redis               running             0.0.0.0:6380->6379/tcp, :::6380->6379/tcp
```

logs

```
docker-compose logs rabbitmq
```

```
docker-compose logs redis
```

docker compose (web)

```
cd /src/quantz-web/
docker-compose up -d
docker-compose ps

$ docker-compose ps
NAME                             COMMAND                  SERVICE             STATUS              PORTS
quantz-web-mongodb-1             "docker-entrypoint.s…"   mongodb             running             0.0.0.0:27017->27017/tcp, :::27017->27017/tcp
quantz-web-rabbitmq-web-1        "docker-entrypoint.s…"   rabbitmq-web        created
quantz-web-redis-accessdb-1      "docker-entrypoint.s…"   redis-accessdb      running             0.0.0.0:6376->6376/tcp, :::6376->6376/tcp, 6379/tcp
quantz-web-redis-results-web-1   "docker-entrypoint.s…"   redis-results-web   created
quantz-web-redis-session-1       "docker-entrypoint.s…"   redis-session       running             0.0.0.0:6379->6379/tcp, :::6379->6379/tcp
```

check

setup daemon

uwsgi

```
sudo ln -s /src/quantz-web/web-server/uwsgi/uwsgi.service /etc/systemd/system/uwsgi.service
sudo systemctl daemon-reload

cd /src/quantz-web/web-server
. ./etc/restart.sh uwsgi
```

nginx

```
sudo apt update
sudo apt install nginx
```

```
sudo ln -s /src/quantz-web/web-server/nginx/nginx.service /etc/systemd/system/nginx.service
sudo systemctl daemon-reload

sudo nginx -t -c /src/quantz-web/web-server/nginx/nginx.conf

cd /src/quantz-web/web-server
. ./etc/restart.sh nginx
```

check

```
sudo journalctl -u nginx
sudo nginx -t -c /src/quantz-web/web-server/nginx/nginx.conf
curl http://localhost:8004
```

vectordb_server

```
sudo ln -s /src/quantz-web/vectordb_server/vectordb_server.service /etc/systemd/system/vectordb_server.service
sudo systemctl daemon-reload

sudo systemctl enable vectordb_server.service
sudo systemctl start vectordb_server.service

cd /src/quantz-web/vectordb_server
. ./restart.sh

sudo journalctl -fu vectordb_server.service --output cat
```

billing_scheduler

```
sudo ln -s /src/quantz-web/web-server/web_tasks_server/service/billing_scheduler.service /etc/systemd/system/billing_scheduler.service
sudo systemctl daemon-reload

sudo systemctl enable billing_scheduler.service
sudo systemctl start billing_scheduler.service

cd /src/quantz-web/web-server/
cd web_tasks_server/service
. ./restart.sh billing_scheduler
```

process_chatdata

```
sudo ln -s /src/quantz-web/web-server/web_tasks_server/service/process_chatdata.service /etc/systemd/system/process_chatdata.service
sudo systemctl daemon-reload

sudo systemctl enable process_chatdata.service
sudo systemctl start process_chatdata.service

cd /src/quantz-web/web-server/
cd web_tasks_server/service
. ./restart.sh process_chatdata
```

```
 sudo apt install tmux
```

workers web tasks (billing_scheduler, process_chatdata)

```
cd /src/quantz-web/web-server
cd web_tasks_server/service
. ./logs.sh
```

*

supercom2はsshd_configがsupercom3と同じ設定だが毎回sshでパスワードを要求されるので解除した

permission

```
sudo chown -R kaz:kaz ~/.ssh
sudo chmod 600 ~/.ssh/authorized_keys
sudo chmod 700 ~/.ssh
```

set pub keys 

```
vim ~/.ssh/authorized_keys
```

update sshd conf

```
sudo vim /etc/ssh/sshd_config

PubkeyAuthentication yes
PasswordAuthentication no
```

restart sshd * 切断されるので注意 (他の接続を確保しておく)

```
sudo systemctl restart sshd
```

login

```
vim ~/.ssh/config

Host supercom2
    HostName 153.174.160.217
    Port 6666
    User kaz
    IdentityFile ~/.ssh/id_supercom3L

ssh -v supercom2
```

Issue: no module name apt_pkg
