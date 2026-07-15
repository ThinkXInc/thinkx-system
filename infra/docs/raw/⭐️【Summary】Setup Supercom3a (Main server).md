# ⭐️【Summary】Setup Supercom3a (Main server)

_created: 20230510T090220Z / updated: 20250425T061200Z_

timezone

```
sudo timedatectl set-timezone UTC
timedatectl
```

essential packages

```
sudo apt update
sudo apt install curl
```

```
sudo apt-get install -y python3-dev portaudio19-dev libffi-dev libssl-dev libsqlite3-dev wget
```

```
sudo apt install libbz2-dev
sudo apt install liblzma-dev
```

*required for python bz2, lzma

utilities

```
sudo apt-get install -y screen sox
```

cuda, cudnn

supercom3: install cuda, driver cudnn (ubuntu2204,  x86_64, cuda12.1)

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
sudo apt install git
sudo apt install git-lfs
git config --global user.name "kazukiotsuka"
git config --global user.email otsuka.kazuki@googlemail.com
cd ~/.ssh
ssh-keygen -t ed25519 -C "otsuka.kazuki@googlemail.com"
Generating public/private ed25519 key pair.
Enter file in which to save the key (/root/.ssh/id_ed25519): id_github
Enter passphrase (empty for no passphrase):
Enter same passphrase again:

vim ~/.ssh/id_github.pub
(register to github)

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

push, pull

```
vim ~/.bashrc

alias pull='git pull --rebase origin master'
alias push='git push --rebase origin master'

source ~/.bashrc
```

Python

supercom3: Install Python3 on Linux (Ubuntu)

```
sudo apt update
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev
 libbz2-dev liblzma-dev
cd ~/Downloads
wget https://www.python.org/ftp/python/3.9.6/Python-3.9.6.tgz
tar -xf Python-3.9.6.tgz
cd Python-3.9.6/
./configure --enable-optimizations
make -j 30  # replace "2" with the number of cores on your machine
sudo make altinstall
python3.9 -c "import bz2" # success if it shows nothing
python3.9 -c "import _lzma" # success if it shows nothing
```

*
sudo apt install libbz2-dev
  
sudo apt install liblzma-dev
 
が事前にbz2のために必要

*やり直す場合

```
make clean
make distclean
sudo rm -rf Python-3.9.6
tar -xf Python-3.9.6.tgz
あとは同じ
```

```
PYTHON3_PATH=$(which python3)
PYTHON3_9_PATH=$(which python3.9)
sudo rm $PYTHON3_PATH
sudo ln -s $PYTHON3_9_PATH $PYTHON3_PATH
```

Go lang

開発記録: localでtrustedな証明書を生成しTLSをlocalhostで行う

```
sudo apt install golang-go
sudo apt install libnss3-tools mkcert
```

```
cd /path/to/proj
mkcert -install
mkcert example.com "*.example.com" example.test localhost 127.0.0.1 ::1
```

Others

supercom3: autoenv

```
sudo apt install curl
curl -#fLo- 'https://raw.githubusercontent.com/hyperupcall/autoenv/master/scripts/install.sh' | sh
echo 'source ~/.autoenv/activate.sh' >> ~/.bashrc
echo 'export AUTOENV_ENV_FILENAME=.autoenv' >> ~/.bashrc
echo 'export AUTOENV_ENV_LEAVE_FILENAME=.autoenv_leave' >> ~/.bashrc
source ~/.bashrc
```

supercom3: Network check

```
sudo apt install inetutils-traceroute speedtest-cli
```

Python, FLAC: FLAC encoding

```
sudo apt update
sudo apt install ffmpeg
```

```
vim ~/.bashrc

# history
export HISTSIZE=10000
export HISTFILESIZE=10000
```

*1000, 2000 in default

(6/9)

・add  libbz2-dev to Python installation (to enable _bz2)

docker

```
sudo snap install docker
sudo apt  install docker-compose
```

docker auto run

```
sudo systemctl is-enabled docker
```

rabbitmmq

```
sudo apt install librabbitmq-dev
sudo apt install autoconf automake libtool python3-dev
```

Repository

```
cd /src
git clone git@github.com:ThinkXInc/quantz.git
```

Update all submodules

```
cd /src/quantz
git submodule init
git submodule update --remote --recursive
```

workspace shortcut 

```
cd ~
vim quantz-workspace.sh -c 'cd /src/quantz'
```

venv

```
cd /src/quantz/processing-server
python3.9 -m venv venv
. ./venv/bin/activate
/src/quantz/processing-server/venv/bin/python3.9 -m pip install --upgrade pip
pip install -r requirements.txt
```

Local Development

*Local DB

Supercom3 (Main server) Local DB

```
cd /src/quantz
vim .env
```

.env(local)

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
MONGO_DB_HOST=localhost
MONGO_DB_PORT=27017
MONGO_DB_USER=user
MONGO_DB_PASSWORD=<REDACTED>
MONGO_DB_NAME=quantz

## LLM

# Model Checkpoint
#llama2
#LLM_CHECKPOINT=/src/hfmodels/llama-2-13b-chat
#LLM_MAX_TOKENS=64
#LLM_MAX_CONTEXT=4096
#llama3
LLM_CHECKPOINT=/src/hfmodels/llama-3-8b-instruct
LLM_MAX_TOKENS=128
LLM_MAX_CONTEXT=8192

# Search Context
N_SEARCH_CONTEXT=2

# RabbitMQ LLM 
RABBITMQ_LLM_USER=guest
RABBITMQ_LLM_HOST=localhost
RABBITMQ_LLM_PORT=5672
RABBITMQ_LLM_PASSWORD=<REDACTED>
RABBITMQ_LLM_DATA_PATH=/var/lib/rabbitmq
RABBITMQ_LLM_LOG_PATH=/var/log/rabbitmq

# Redis Results LLM
REDIS_RESULTS_LLM_HOST=localhost
REDIS_RESULTS_LLM_PORT=6381
REDIS_RESULTS_LLM_LOGLEVEL=debug
REDIS_RESULTS_LLM_DB_NUMBER=0
REDIS_RESULTS_LLM_EXPIRATION_TIME_SEC=180
REDIS_RESULTS_LLM_DATA_PATH=/var/lib/redis_llm
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
REDIS_RESULTS_PROCESSING_DATA_PATH=/var/lib/redis_processing

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
REDIS_RESULTS_VECTORDB_DATA_PATH=/var/lib/redis_vectordb

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

```
ln -s /src/quantz/.env /src/quantz/local/.env  # docker-compose can recognize only the same or under the directory
```

```
sudo usermod -aG docker ${USER}
```

```
docker pull qdrant/qdrant
```

```
cd /src/quantz/local
docker-compose up -d
```

*Permission Deniedの場合一度再ログインが必要かも

Check if running

```
docker-compose ps && docker ps -f name=redis-session -f name=redis-accessdb -f name=mongodb -f name=rabbitmq-shared -f name=redis-results-shared -f name=redis-results-llm -f name=redis-results-processing -f name=redis-local-chatdb -f name=qdrant --format "table {{.Names}}\t{{.Status}}"
```

NAMES                              STATUS

local_redis-results-shared_1       Up 2 minutes

local_redis-results-llm_1          Up 2 minutes

local_redis-accessdb_1             Up 2 minutes

local_rabbitmq-shared_1            Up 2 minutes

local_mongodb_1                    Up 2 minutes

local_redis-session_1              Up 2 minutes

local_redis-local-chatdb_1         Up 2 minutes

local_redis-results-processing_1   Up 2 minutes

local_qdrant_1                     Up 54 seconds

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

supercom3: Setup jptextparser (+ Install Mecab  iPadicNeologd) to Ubuntu

llm

```
cd /src/quantz/processing-server/llm
python -m venv venv
pip install -r requirements.txt
```

Setup Daemon and Run

gateway-server

```
sudo ln -s /src/quantz/gateway-server/gateway-server.service /etc/systemd/system/gateway-server.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable gateway-server.service
sudo systemctl start gateway-server.service
```

check

```
sudo journalctl -fu gateway-server.service --output cat
```

unix_socket_server

```
sudo ln -s /src/quantz/processing-server/unix_socket_server/unix_socket_server.service /etc/systemd/system/unix_socket_server.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable unix_socket_server.service
sudo systemctl start unix_socket_server.service
```

check

```
sudo journalctl -fu unix_socket_server.service --output cat
```

LLM

```
sudo ln -s /src/quantz/processing-server/llm_server/llm_server.service /etc/systemd/system/llm_server.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable llm_server.service
sudo systemctl start llm_server.service
```

```
sudo journalctl -fu llm_server.service --output cat
```

Workers

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/handle_llm_general_task_outputs.service /etc/systemd/system/handle_llm_general_task_outputs.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/handle_llm_outputs.service /etc/systemd/system/handle_llm_outputs.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/llm_general_task.service /etc/systemd/system/llm_general_task.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/process_transcript.service /etc/systemd/system/process_transcript.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/respond.service /etc/systemd/system/respond.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/transcribe.service /etc/systemd/system/transcribe.service

# Enable services to start at boot
sudo systemctl enable handle_llm_general_task_outputs.service
sudo systemctl enable handle_llm_outputs.service
sudo systemctl enable llm_general_task.service
sudo systemctl enable process_transcript.service
sudo systemctl enable respond.service
sudo systemctl enable transcribe.service

# Start the services
sudo systemctl start handle_llm_general_task_outputs.service
sudo systemctl start handle_llm_outputs.service
sudo systemctl start llm_general_task.service
sudo systemctl start process_transcript.service
sudo systemctl start respond.service
sudo systemctl start transcribe.service
```

check

```
sudo journalctl -fu transcribe.service --output cat
```

```
sudo journalctl -fu process_transcript.service --output cat
```

```
sudo journalctl -fu respond.service --output cat
```

```
sudo journalctl -fu respond.service --output cat
```

```
sudo journalctl -fu respond.service --output cat
```

```
sudo journalctl -fu llm_general_task.service --output cat  -n 1000 -f
```

```
sudo journalctl -fu handle_llm_general_task_outputs.service --output cat -n 1000 -f
```

Quantz Web 

shared .env(local)

```
ln -s /src/quantz/.env /src/quantz-web/.env
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

cd /src/quantz-web/web-server
. ./etc/restart.sh nginx reload
```

check

```
sudo journalctl -u nginx
sudo nginx -t -c /src/quantz-web/web-server/nginx/nginx.conf
curl http://localhost:8001
```

check

```
ssh supercom3a
curl -I http://localhost:8000/favicon.ico
```

補足

Using cached deepspeed-0.15.1-py3-none-any.whl

ERROR: Cannot install -r requirements.txt (line 141), -r requirements.txt (line 147), -r requirements.txt (line 150), -r requirements.txt (line 183), -r requirements.txt (line 2), -r requirements.txt (line 207), -r requirements.txt (line 217), -r requirements.txt (line 40) and torch==2.1.2 because these package versions have conflicting dependencies.

The conflict is caused by:

    The user requested torch==2.1.2

    accelerate 0.17.1 depends on torch>=1.4.0

    deepspeed 0.15.1 depends on torch

    openai-whisper 20231117 depends on torch

    outlines 0.0.34 depends on torch>=2.1.0

    peft 0.3.0 depends on torch>=1.13.0

    pytorch-lightning 2.2.1 depends on torch>=1.13.0

    stanza 1.1.1 depends on torch>=1.3.0

    torchaudio 2.3.1 depends on torch==2.3.1

正常なシステムで生成したrequirementz.txtを使っても依存関係解決に失敗する

このようなときは絡まったもののうちより重要でないものをrequirementx.txtから削除する

上の場合torchaudioを消す

消しても必要なものはあとからinstall

```
pip install qdrant-client
```