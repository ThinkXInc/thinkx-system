# 🍑【Summary】 thinkxinc.com

_created: 20250410T082246Z / updated: 20250410T082625Z_

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
sudo systemctl restart uwsgi_thinkx.service
```

Logs
