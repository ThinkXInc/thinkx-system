# basic setup for webserver
#
# prerequisites:
#  - setup_user.sh
#

# hostname
 
HN=web1; [ "$ENVX" = staging ] && HN=web1-stg
sudo hostnamectl set-hostname "$HN"
echo 'preserve_hostname: true' | sudo tee /etc/cloud/cloud.cfg.d/99-hostname.cfg > /dev/null
 

export NEEDRESTART_MODE=a   # apt 中の needrestart 対話を抑止(サービス再起動は自動)

# essential packages

sudo apt update
sudo apt install -y curl
sudo apt-get install -y python3-dev python3-venv portaudio19-dev libffi-dev libssl-dev libsqlite3-dev wget screen vim net-tools

# bashrc

cat >> ~/.bashrc <<'EOF'
alias pip=pip3
alias push="git push origin master"
alias pull="git pull --rebase origin master"
alias add="git add ."
alias st="git status"
export PATH=/usr/local/bin/mongodb/bin:$PATH
export HISTSIZE=10000
export HISTFILESIZE=10000
EOF

# Git

sudo apt install -y git
git config --global user.name "kazukiotsuka"
git config --global user.email otsuka.kazuki@googlemail.com

## *account 鍵は setup_user.sh の Deploy key(repo 単位 read-only)で実現するため以下は行わない
# cd ~/.ssh
# ssh-keygen -t ed25519 -C "otsuka.kazuki@googlemail.com"   # -> id_github
# sudo apt-get update
# sudo apt-get install keychain
# (keychain --eval --agents ssh id_github)
# vim ~/.ssh/config
#   Host github.com
#      IdentityFile ~/.ssh/id_github
#      Port 22
# ssh -T git@github.com

git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage 'reset HEAD --'

sudo apt install -y git-lfs

# Python
# supercom3: Install Python3 on Linux (Ubuntu)

sudo apt update
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libbz2-dev liblzma-dev
cd /tmp
wget https://www.python.org/ftp/python/3.9.6/Python-3.9.6.tgz
tar -xf Python-3.9.6.tgz
cd Python-3.9.6/
./configure --enable-optimizations --with-ensurepip=upgrade --prefix=/usr/local
make -j "$(nproc)"
sudo make altinstall
python3.9 --version

#* /usr/local/bin/にインストールされると/usr/bin/pythonがエラーを起こす(/usr/bin/上でimport しようとしてもないため) ->
# ./configure --enable-optimizations --prefix=/usr
#  -> この方法はシステムのpythonを上書きするのでよくない -> /usr/localを指定
# *python3をpython3.9にリンクさせない 単に python3.9 -m venv venvでvenv内でpython3.9を使えばいい

# Redis Cli

sudo apt install -y redis-tools

# Install Docker
# cf. "Install docker to Ubuntu 22.04"

sudo apt-get remove -y docker.io docker-doc docker-compose podman-docker containerd runc
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --yes --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker run hello-world

# install docker-compose

sudo curl -L "https://github.com/docker/compose/releases/download/v2.9.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# add kaz to docker group

sudo usermod -aG docker kaz
## *newgrp docker は新シェルに入って止まるため行わない(反映は再ログイン。script 内は sudo docker)
# newgrp docker

# Qdrant

sudo docker pull qdrant/qdrant
## *run qdrant server (起動は docker-compose 側。単体起動する場合)
# docker run -p 6333:6333 \
#     -v $(pwd)/qdrant_storage:/qdrant/storage \
#     qdrant/qdrant

# MongoDB

sudo apt-get install -y gnupg curl
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg --yes -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

## enable mongosh command

sudo apt-get install -y mongodb-org-shell

# Create Admin User Group

sudo groupadd serveradmins
sudo usermod -a -G serveradmins kaz

# Working Directory

sudo mkdir /src
sudo chown kaz:serveradmins /src

# Install npm

sudo apt install -y npm

# npx npm-run-all … をsudoなしで実行できるようにする (kaz の ~/.npm-global)

sudo -u kaz -H mkdir -p /home/kaz/.npm-global
sudo -u kaz -H npm config set prefix '/home/kaz/.npm-global'
echo 'export PATH=/home/kaz/.npm-global/bin:$PATH' | sudo -u kaz tee -a /home/kaz/.bashrc > /dev/null

# update npm

sudo npm install -g n
sudo n stable
sudo npm install -g npm

# Autoenv  (*installer が npm -g を使うため npm 更新後に実行。EACCES 対策で sudo(原本注記: permission denied が出たら sudo をつけて実行する))

curl -#fLo- 'https://raw.githubusercontent.com/hyperupcall/autoenv/master/scripts/install.sh' | sudo sh
echo 'source ~/.autoenv/activate.sh' >> ~/.bashrc
echo 'export AUTOENV_ENV_FILENAME=.autoenv' >> ~/.bashrc
echo 'export AUTOENV_ENV_LEAVE_FILENAME=.autoenv_leave' >> ~/.bashrc
## * ~/.autoenv/activate.sh が作られなければ手動でこれを設置し source ~/.bashrc

# install globally  (/usr/local/bin に入れて sudo -u kaz 実行時も PATH が通るようにする)

sudo npm install -g @babel/cli less-watch-compiler npm-run-all

# gulp  (*apt に gulp パッケージは無いため npm -g の gulp-cli を使う)

sudo npm install -g gulp-cli

# nginx

sudo apt update
sudo apt install -y nginx

# tmux

sudo apt install -y tmux

# sshd  (AWS は EC2 keypair 管理で PasswordAuthentication は既定 no。authorized_keys も cloud-init が設置済みのため以下は不要)

# sudo chown -R kaz:kaz ~/.ssh
# sudo chmod 600 ~/.ssh/authorized_keys
# sudo chmod 700 ~/.ssh
# vim ~/.ssh/authorized_keys
# sudo vim /etc/ssh/sshd_config
#   PubkeyAuthentication yes
#   PasswordAuthentication no
# sudo systemctl restart sshd  # * 切断されるので注意 (他の接続を確保しておく)

# check

python3.9 --version
node -v
npm -v
sudo docker --version
docker-compose --version
mongod --version
nginx -v
gulp --version
# verify  (主要ツールの存在 + hostname が ENVX に一致)
HNV=web1
[ "$ENVX" = staging ] && HNV=web1-stg
command -v python3.9 > /dev/null && command -v node > /dev/null && command -v nginx > /dev/null && command -v mongod > /dev/null && [ "$(hostname)" = "$HNV" ] && printf '\033[32mOK: setup_webserver 完了(python3.9/node/nginx/mongod あり・hostname=%s)\033[0m\n' "$HNV" || printf '\033[31mFAIL: setup_webserver 要確認 python3.9=%s node=%s nginx=%s mongod=%s hostname=%s(期待=%s)\033[0m\n' "$(command -v python3.9 || echo なし)" "$(command -v node || echo なし)" "$(command -v nginx || echo なし)" "$(command -v mongod || echo なし)" "$(hostname)" "$HNV"
