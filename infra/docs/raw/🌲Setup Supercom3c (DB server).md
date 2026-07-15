# 🌲Setup Supercom3c (DB server)

_created: 20240411T095011Z / updated: 20250425T035717Z_

まずこの一部を実行

⭐️【Summary】supercom3: setup & installation

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
./configure --enable-optimizations --prefix=/usr/local
make -j 30  # replace "2" with the number of cores on your machine
sudo make altinstall
python3.9 -c "import bz2" # success if it shows nothing
python3.9 -c "import _lzma" # success if it shows nothing
```

* bz2, lzmaはエラーだがとりあえず無視

* /usr/local/bin/にインストールされると/usr/bin/pythonがエラーを起こす(/usr/bin/上でimport しようとしてもないため) -> --prefix=/usrをつけて明示的に/usr/binを指定 
./configure --enable-optimizations --prefix=/usr
 -> この方法はシステムのpythonを上書きするのでよくない -> /usr/localを指定

```
PYTHON3_PATH=$(which python3)
PYTHON3_9_PATH=$(which python3.9)
sudo rm $PYTHON3_PATH
sudo ln -s $PYTHON3_9_PATH $PYTHON3_PATH
```

```
sudo ln -s /usr/bin/python3.9 /usr/bin/python3
sudo ln -s /usr/bin/python3 /usr/bin/python
```

Redis Cli

```
sudo apt install -y redis-tools
```

MongoDB Client

```
sudo apt update
sudo apt install mongodb-clients
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

Install Docker

cf. 
Install docker to Ubuntu 22.04

*このインストール方法はだめかもしれないのでdocker-compose up -dでエラーが出たら最下のトラブルシューティングを確認

uninstall old versions

```
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done
```

```
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
```

```
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
```

```
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

```
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

```
sudo apt-get update
```

```
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

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

Enable auto restart docker process

```
sudo systemctl is-enabled docker
```

* add 
restart: unless-stopped
  to docker-compose.yml for each service

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

enable mongo command

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
git clone git@github.com:ThinkXInc/quantz-db.git
cd quantz-db
git submodule update --init --recursive
cd backup_system
python3.9 -m venv venv
. ./venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Set host machine configuration

```
cd /src/quantz-db
. ./setup_host.sh
```

含むもの

*redisのovercommit_memory=1に <- 永続化に特に優位

Celery log

```
sudo mkdir /var/log/celery
sudo chown -R kaz:serveradmins /var/log/celery
sudo chmod 755 /var/log/celery
```

Color log

```
sudo apt-get install ccze
```

Docker compose up -dが上手くいかない時

address already in use

-> 

```
sudo lsof -i :{PORT}
sudo kill {PID}
```

でkillして再度docker-compose up -d

特に/var/lib/{db} is read only 

-> 下記の手順でdockerを消して入れ直す

*詳しくは 
Supercom3 (Main server) Local DB

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

mongo user

まずdocker-compose up -dで

```
environment:    - MONGO_INITDB_ROOT_USERNAME=${MONGO_DB_USER}    - MONGO_INITDB_ROOT_PASSWORD=${MONGO_DB_PASSWORD}    - MONGO_INITDB_DATABASE=${MONGO_DB_NAME}
```

の情報を使って最初のadminユーザーが作成されていること

さらに

```
mongosh "mongodb://user:pass@localhost:27017/quantz"
```

を
?authSource=admin
なしで実行できるようにしたいので(つまりadminユーザーでなくUSER_NAME=userで実行できるようにしたいので)下記で設定する

```
mongosh "mongodb://user:pass@localhost:27017/quantz?authSource=admin"
use quantz
db.createUser({
  user: "user",
  pwd: "pass",
  roles: [{ role: "readWrite", db: "quantz" }]
});
```