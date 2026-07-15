# サーバー初期構築(原本)

supercom2/3 の初期セットアップ手順。essential packages, bashrc, git(ssh鍵),
python3.9(ソースビルド, /usr/local), redis-tools, autoenv, docker, qdrant,
mongodb, /src 作業ディレクトリ, venv + pip, npm/gulp フロントビルド,
uwsgi/nginx/vectordb/billing_scheduler/process_chatdata の systemd 登録。

主要コマンド(抜粋):
```
sudo apt-get install -y python3-dev python3-venv build-essential libffi-dev libssl-dev ...
# python3.9 は ./configure --prefix=/usr/local でソースビルド(システム python を上書きしない)
sudo mkdir /src && sudo chown kaz:serveradmins /src
python3.9 -m venv venv && pip install -r requirements.txt
sudo ln -s /src/<repo>/web-server/uwsgi/uwsgi.service /etc/systemd/system/uwsgi.service
sudo systemctl daemon-reload && systemctl enable --now uwsgi.service
```

.env に本番の認証情報(AWS/Stripe 等)が平文で存在 → 移行時に SES は IAM ロール化し
平文アクセスキーを廃止(改善候補)。

> 移行後: setup/web-setup.sh がこの手順を AWS 非依存 bash に再構成。libcommon の
> submodule 取得は vendoring 済みのため不要。
