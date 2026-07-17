# loadbalancer
#
# prerequisites:
#  - setup_user.sh
#  - check_deploykey.py thinkx-system が OK + setup_monorepo.sh 済み
#  - push_secrets.sh(certs/deploykeys)
#  - push_env.sh loadbalancer(/tmp/loadbalancer.env。真実は loadbalancer/.env)
#

export NEEDRESTART_MODE=a   # apt 中の needrestart 対話を抑止(サービス再起動は自動)

# hostname

sudo hostnamectl set-hostname lb
echo 'preserve_hostname: true' | sudo tee /etc/cloud/cloud.cfg.d/99-hostname.cfg > /dev/null

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

# Autoenv  (*LB は npm 無しのため installer は ~/.autoenv 方式で動く。permission denied が出たら sudo をつけて実行する(原本注記))

curl -#fLo- 'https://raw.githubusercontent.com/hyperupcall/autoenv/master/scripts/install.sh' | sh
echo 'source ~/.autoenv/activate.sh' >> ~/.bashrc
echo 'export AUTOENV_ENV_FILENAME=.autoenv' >> ~/.bashrc
echo 'export AUTOENV_ENV_LEAVE_FILENAME=.autoenv_leave' >> ~/.bashrc

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

# MongoDB

sudo apt-get install -y gnupg curl
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg --yes -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

## enable mongosh command

sudo apt-get install -y mongodb-org-shell

# tmux

sudo apt install -y tmux

sudo apt install -y iftop sysstat nload traceroute

# TLS  (証明書はローカルの secrets ディレクトリに保管し、EC2 作成のたびに /tmp へアップロードしてから流す)

## install certbot  (*証明書は LB 上で certbot --dns-route53 により取得する(D-22)。Route53 権限は terraform の IAM ロールで付与済みが前提)
sudo apt update
sudo apt install certbot
sudo apt install python3-certbot-nginx
sudo apt-get install -y python3-certbot-dns-route53  # added for terraform automation

## 保管場所: thinkx-system/infra/certs/lb-certs.tgz(★秘密鍵を含むため infra/certs/ は .gitignore 必須・コミット禁止)
## (初回のみ・オンプレ supercom3L で作成。★事前に grep -rh 'ssl_certificate' /src/loadbalancer/ で参照される証明書を全列挙し、漏れなく含める):
##   sudo tar czf /tmp/lb-certs.tgz /etc/letsencrypt /etc/ssl/private /etc/ssl/certs/thinkxinc.com.crt /etc/ssl/certs/sixthsai.crt /etc/ssl/certs/jessicas.online.crt
## 配布は push_secrets.sh(secrets.tgz に certs 同梱)。lb-certs.tgz は絶対パス(/etc/letsencrypt 等)で作る
tar xzf /tmp/secrets.tgz -C /tmp certs/lb-certs.tgz
sudo tar xzf /tmp/certs/lb-certs.tgz -C /

sudo groupadd sslgroup
sudo usermod -a -G sslgroup kaz

## *gid はマシンごとに異なるため、展開後に所有権と権限を張り直す
sudo chown root:sslgroup /etc/ssl/private/thinkxinc.com.key
sudo chown root:sslgroup /etc/ssl/certs/thinkxinc.com.crt
sudo chmod 644 /etc/ssl/certs/thinkxinc.com.crt
sudo chmod 640 /etc/ssl/private/thinkxinc.com.key

# (TLS sixths.ai)

sudo chown root:sslgroup /etc/ssl/private/custom.key
sudo chown root:sslgroup /etc/ssl/certs/sixthsai.crt
sudo chmod 644 /etc/ssl/certs/sixthsai.crt
sudo chmod 640 /etc/ssl/private/custom.key

# install nginx

sudo apt update
sudo apt install -y nginx


## TLS 自動更新の reload hook  (renew 自体は apt certbot 標準の systemd timer が無人実行(D-25)。更新後の証明書を nginx に反映させる)
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh > /dev/null <<'EOF'
#!/bin/bash
systemctl reload nginx
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

# permissions

sudo chown www-data:www-data /var/log/nginx/access.log
sudo chown www-data:www-data /var/log/nginx/error.log
sudo chmod 664 /var/log/nginx/access.log
sudo chmod 664 /var/log/nginx/error.log
sudo mkdir -p /run/nginx
sudo chown www-data:www-data /run/nginx

# make run group

sudo groupadd serveradmins
sudo usermod -a -G serveradmins kaz

# make source directory

sudo mkdir /src
sudo chown kaz:serveradmins /src

# clone repo  (前提: check_deploykey.py loadbalancer が OK)
## *conf.d の proxy_pass は web1.supercom.internal(内部 DNS・D-28/D-31)で repo にコミット済みが前提。EC2 側でのパッチはしない

# (monorepo 前提。clone と symlink は setup_monorepo.sh が行う)
[ -e /src/loadbalancer/nginx.conf ] || printf '\033[31mFAIL: /src/loadbalancer が無い。先に setup_monorepo.sh を流す\033[0m\n'

# symlink

sudo ln -sf /src/loadbalancer/nginx.service /etc/systemd/system/nginx.service
sudo systemctl daemon-reload

# install screen

sudo apt install -y screen

# install multitail

sudo apt-get install -y multitail

# staging basic auth  (push_env.sh で配った /tmp/loadbalancer.env の user/pass から htpasswd 生成。644=nginx worker が読める)
set -a; . /tmp/loadbalancer.env; set +a
printf '%s:%s\n' "$STAGING_BASIC_AUTH_USER" "$(openssl passwd -apr1 "$STAGING_BASIC_AUTH_PASS")" | sudo tee /etc/nginx/.htpasswd_staging > /dev/null
sudo chmod 644 /etc/nginx/.htpasswd_staging

# 起動

sudo nginx -t -c /src/loadbalancer/nginx.conf
sudo systemctl restart nginx

# verify
systemctl is-active --quiet nginx && printf '\033[32mOK: lb nginx up\033[0m\n' || printf '\033[31mFAIL: lb nginx %s\033[0m\n' "$(systemctl is-active nginx)"