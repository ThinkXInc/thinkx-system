# ✴️【Summary】Run Web App Server (thinkx, NNTM)

_created: 20250317T032814Z / updated: 20260701T122144Z_

Build & Run App

build watcher - front end app　🪐 

```
cd /src/thinkx/web-server
cd views
. ./watchappviews.sh
```

uwsgi log 
🌃【Summary】UWSGI Commands
 🪐 

```
sudo journalctl -fu uwsgi_thinkx.service --output cat -n 3000
```

restart uwsgi 🪐 

```
cd /src/thinkx/web-server
sudo systemctl restart uwsgi_thinkx.service
```

Logs
