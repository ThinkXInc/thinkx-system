# サイト要件 Web Sites Requirements

Web サイトを追加・デプロイするためにディレクトリ内に必要な配置物と手続きのチェックリスト．
サイトのキー(レポジトリ名)を "site1"，公開ドメインを "site1.com"，backend ポートを {port} とする．

### Requirements
- site1/.env があり FLASK_APP_SECRET_KEY, ENV に値がセットされている
- .gitignoreに.envが書かれている
- site1/web-server/config.py が PRJ_ROOT/.env を読む
- site1/web-server/requirements.txt, site1/web-server/venvでpythonの依存関係
- site1/web-server/uwsgi/uwsgi_site1.service, uwsgi.ini
    - socket=/tmp/uwsgi_site1.sock
- site1/web-server/nginx/conf.d/site1.conf 
    - listen {port}
    - server_name site1.com
    - uwsgi_pass unix:/tmp/uwsgi_site1.sock．
- site1/web-server/views/src/js, src/less/main.less 
    - babel/lessc でmain.lessからviews/css/に書き出される
- gitignoreに実生成物 views/js, views/css, views/video が追加されている
- web-server/libcommon が vendoring として配置されている
- deploy key が GitHub のレポジトリに登録されている
    - GitHub → {TEAM}/{repo} → Settings → Deploy keys
    - Allow write は外す

### TLS
- certbot --dns-route53 で *.site1.com のワイルドカード証明書 /etc/letsencrypt/live/site1.com/ が生成されている

### Setup
- ../infra/setup/setup_site1.sh があること
    - prerequisites: 
        - setup_user.sh
        - setup_webserver.sh
        - check_deploykey.py site1
        - push_env.sh site1
    - setup_thinkx.sh を基本型とする 
        - clone→.env→venv→front build→uwsgi_site1→verify
- ../nginx-web-root/nginx.conf に include /src/site1/web-server/nginx/conf.d/*.conf; があること．

### DNS
- Route53 > ホストゾーン > 対応するドメインの staging.site1.com の A レコードに {EIP} がセットされていること．

### Run
- ../infra/run/に下記があること
    - run_site1.sh 
    - stop_site1.sh 
    - restart_site1.sh

### Deploy
(webserver)
- 1. push_secrets.sh {host}(certs/deploykeys)
- 2. push_env.sh {host} site1(.env)
- 3. push_assets.sh {host} site1(video・あれば)．
- 4. check_deploykey.py site1 が OK．
- 5. ssh {host} 'bash -s' < ../infra/setup/setup_site1.sh(受け入れ = ルートゴールデン)．
(loadbalancer)
- 1. ../loadbalancer/conf.d/staging.site1.com.confに以下を書く
    - auth_basic + proxy_set_header Host site1.com + proxy_pass web1:{port}
- 2. nginx reload．
