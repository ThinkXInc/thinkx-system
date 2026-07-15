# quantz-web
#
# prerequisites:
#  - setup_user.sh
#  - setup_webserver.sh
#  - check_deploykey.py が quantz-web / llm / simplicity とも OK
#  - push_env.sh quantz-web(/tmp/quantz-web.env。真実は quantz-web/.env)
#

export NEEDRESTART_MODE=a   # apt 中の needrestart 対話を抑止(サービス再起動は自動)

# Clone Quantz DB Repository  (前提: check_deploykey.py が quantz-web / llm / simplicity とも OK)

cd /src
sudo -u kaz git clone git@github-quantz-web:ThinkXInc/quantz-web.git

# Create venv and install pip manually

cd /src/quantz-web/web-server
sudo -u kaz python3.9 -m venv --without-pip venv
sudo -u kaz curl -s https://bootstrap.pypa.io/pip/3.9/get-pip.py -o get-pip.py
sudo -u kaz ./venv/bin/python get-pip.py
sudo -u kaz ./venv/bin/pip install --upgrade pip

# Install Python dependencies

sudo -u kaz ./venv/bin/pip install -r requirements.txt

# submodule 用 Deploy key の URL 変換  (.gitmodules は素の github.com URL のため、kaz の git 設定で別名へ透過変換する。鍵は上の check_deploykey.py で配置済み)

sudo -u kaz -H git config --global url."git@github-libcommon:ThinkXInc/libcommon.git".insteadOf "git@github.com:ThinkXInc/libcommon.git"
sudo -u kaz -H git config --global url."git@github-llm:ThinkXInc/llm.git".insteadOf "git@github.com:ThinkXInc/llm.git"
sudo -u kaz -H git config --global url."git@github-simplicity:ThinkXInc/simplicity.git".insteadOf "git@github.com:ThinkXInc/simplicity.git"

# Update all submodules  (libcommon ×2 / llm / simplicity)

cd /src/quantz-web
sudo -u kaz git submodule init
sudo -u kaz git submodule update --remote --recursive

# Install node_modules

cd /src/quantz-web/web-server/views
sudo -u kaz npm install

# run

cd /src/quantz-web/web-server/views
sudo -u kaz npx npm-run-all --parallel compile:views:js compile:views:css copy:simplicity:js copy:simplicity:css

# watchsimplicity.shが使えるようにする

cd /src/quantz-web/web-server/views/src/js/simplicity
sudo -u kaz npm install

## *watch 系はファイル監視で常駐するため setup では実行しない。開発時に手動:
# cd /src/quantz-web/web-server/views && . ./watchsimplicity.sh
# cd /src/quantz-web/web-server/views && . ./watchappviews.sh

# web-clientでgulpができるようにする

cd /src/quantz-web/web-client
sudo -u kaz npm install

# build simplicity

cd /src/quantz-web/web-server/views/js/simplicity
sudo -u kaz npm install gulp

## *simplicity/node_modulesが全て揃うまで待つ 30分以上かかる

# check global gulp

gulp --version

# run

cd /src/quantz-web/web-client
sudo -u kaz gulp
## *gulp の default task が watch を含む場合ここで常駐して止まる → その場合はビルド task 名を指定に変える(要実機確認)

## *quantz-button.min.jsは現在gulpで自動で生成されないようにしている
## 以下のように最新のバージョンから生成する({version} は実在の番号に置換して手動実行)
# cp /src/quantz-web/web-server/views/js/dist/quantz-button-v{version}.min.js /src/quantz-web/web-server/views/js/dist/quantz-button.min.js

# vectordb_server

cd /src/quantz-web/vectordb_server
sudo -u kaz python3.9 -m venv --without-pip venv
sudo -u kaz curl -s https://bootstrap.pypa.io/pip/3.9/get-pip.py -o get-pip.py
sudo -u kaz ./venv/bin/python get-pip.py
sudo -u kaz ./venv/bin/pip install --upgrade pip
sudo -u kaz ./venv/bin/pip install -r requirements.txt

# setup local db (rabbitmq, redis results)

## ★.env(AWS/Stripe の平文鍵)は quantz-web/.env に置き push_env.sh で配布(D-14)。docker-compose up の前に:
##   (Mac) infra/etc/push_env.sh supercom-web quantz-web
##   (EC2) sudo install -o kaz -g serveradmins -m 640 /tmp/quantz-web.env /src/quantz-web/.env

# docker compose (web)

cd /src/quantz-web
sudo docker-compose up -d
sudo docker-compose ps

# logs  (原本は up の前にあったが、コンテナが無くエラーになるため up の後で確認)

sudo docker-compose logs rabbitmq
sudo docker-compose logs redis

# setup daemon

# uwsgi

sudo ln -sf /src/quantz-web/web-server/uwsgi/uwsgi.service /etc/systemd/system/uwsgi.service
sudo systemctl daemon-reload

cd /src/quantz-web/web-server
. ./etc/restart.sh uwsgi

# nginx  (nginx 本体は setup_webserver.sh で導入済み。ここは repo の service/conf の配線)

sudo ln -sf /src/quantz-web/web-server/nginx/nginx.service /etc/systemd/system/nginx.service
sudo systemctl daemon-reload

sudo nginx -t -c /src/quantz-web/web-server/nginx/nginx.conf

cd /src/quantz-web/web-server
. ./etc/restart.sh nginx

# vectordb_server

sudo ln -sf /src/quantz-web/vectordb_server/vectordb_server.service /etc/systemd/system/vectordb_server.service
sudo systemctl daemon-reload

sudo systemctl enable vectordb_server.service
sudo systemctl start vectordb_server.service

cd /src/quantz-web/vectordb_server
. ./restart.sh

## *follow 表示は常駐するため setup では実行しない。確認は手動:
# sudo journalctl -fu vectordb_server.service --output cat

# billing_scheduler

sudo ln -sf /src/quantz-web/web-server/web_tasks_server/service/billing_scheduler.service /etc/systemd/system/billing_scheduler.service
sudo systemctl daemon-reload

sudo systemctl enable billing_scheduler.service
sudo systemctl start billing_scheduler.service

cd /src/quantz-web/web-server/web_tasks_server/service
. ./restart.sh billing_scheduler

# process_chatdata

sudo ln -sf /src/quantz-web/web-server/web_tasks_server/service/process_chatdata.service /etc/systemd/system/process_chatdata.service
sudo systemctl daemon-reload

sudo systemctl enable process_chatdata.service
sudo systemctl start process_chatdata.service

cd /src/quantz-web/web-server/web_tasks_server/service
. ./restart.sh process_chatdata

# workers web tasks (billing_scheduler, process_chatdata)

## *logs.sh は tail 常駐のため setup では実行しない。確認は手動:
# cd /src/quantz-web/web-server/web_tasks_server/service && . ./logs.sh

# check

cd /src/quantz-web
sudo docker-compose ps
systemctl is-active uwsgi nginx vectordb_server billing_scheduler process_chatdata
sudo nginx -t -c /src/quantz-web/web-server/nginx/nginx.conf
curl -I http://localhost:8004