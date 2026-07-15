# ✴️【Summary】Run Web App Server (Quantz Web) ver.2

_created: 20240329T055153Z / updated: 20250425T035013Z_

Build & Run App

build watcher - simplicity　🪐 

```
cd /src/quantz-web/web-server
cd views
. ./watchsimplicity.sh
```

build watcher - front end app　🪐 

```
cd /src/quantz-web/web-server
cd views
. ./watchappviews.sh
```

uwsgi log 
🌃【Summary】UWSGI Commands
 🪐 

```
sudo journalctl -fu uwsgi.service --output cat -n 3000
```

restart uwsgi 🪐 

```
cd /src/quantz-web/web-server
. ./etc/restart.sh uwsgi
```

Logs

nginx log 
🌃【Summary】Nginx Commands
 🪐 

```
cd /src/quantz-web
cd web-server/nginx
screen -c .screenrc_nginx
```

uwsgi log 
🌃【Summary】UWSGI Commands
 🪐 

```
sudo journalctl -fu uwsgi.service --output cat -n 3000
```

or

```
cd /src/quantz-web
cd web-server/uwsgi
screen -c .screenrc_uwsgi
```

or

```
sudo journalctl -u uwsgi.service --no-pager | tail -n 3000 | less
```

logs vectordb server

```
cd /src/quantz-web/vectordb_server
. ./logs.sh
```

logs web_tasks_server (billing_scheduler, process_chatdata)

```
cd /src/quantz-web/web-server
cd web_tasks_server/service
. ./logs.sh
```

logs system_status (check_congestion)

```
cd /src/quantz-web/web-server
cd system_status/service
. ./logs.sh
```

redis (session) log 🌜

```
cd /src/quantz
cd web-server/redis_session
screen -c .screenrc_redis_session
```

accessdb stats (host)

```
cd /src/quantz
cd accessdb_server
. ./stats_host.sh
```

accessdb stats (host)

```
cd /src/quantz
cd accessdb_server
. ./stats_access.sh
```

mongodb 🌜

```
cd /src/quantz
cd account-server/mongodb
screen -c .screenrc_mongodb
```

🌜 db server (supercom3c)

☀️ main GPU server (supercom3a, b)

🪐 web server (supercom2)

billing_scheduler log

```
sudo journalctl -fu billing_scheduler.service --output cat
```

process_chatdata log

```
sudo journalctl -fu process_chatdata.service --output cat
```

run vectordb celery manually

```
cd /src/quantz-web/vectordb_server
GPU_ID=0 celery -A run:celery_app worker -l info -Q echo,vectordb_save,vectordb_update,vectordb_delete,vectordb_delete_collection,vectordb_create_collection
```

*-Q で指定したtaskしか認識できないので注意

Restart

restart uwsgi 🪐 

```
cd /src/quantz-web/web-server
. ./etc/restart.sh uwsgi
```

restart (reload) nginx

```
cd /src/quantz-web/web-server
cd nginx
. ./restart.sh reload
```

restart vectordb server  ☀️

```
cd /src/quantz-web/vectordb_server
. ./restart.sh
```

restart billing_scheduler ☀️

```
cd /src/quantz-web/web-server/
cd web_tasks_server/service
. ./restart.sh billing_scheduler
```

*-r option 
. ./restart.sh billing_scheduler -r
 reload .service before restarting

restart process_chatdata ☀️

```
cd /src/quantz-web/web-server/
cd web_tasks_server/service
. ./restart.sh process_chatdata
```

restart system_status (check_congestion)

```
cd /src/quantz-web/web-server
cd system_status/service
. ./restart.sh check_congestion
```

Build Quantz Button Source

```
cd web-client
gulp
```

📄 quantz-button.min.js とアップデート方法

DB Server

check if running

```
ssh supercom3c
cd /src/quantz-db
docker-compose ps
```

run

```
ssh supercom3c
cd /src/quantz-db
docker-compose up -d
```

✔ Container quantz-db-redis-session-1            Started  

 ✔ Container quantz-db-redis-chatdata-1           Started    

 ✔ Container quantz-db-redis-interaction-model-1  Started    

 ✔ Container quantz-db-qdrant-1                   Started   

 ✔ Container quantz-db-mongodb-1                  Started                                        

 ✔ Container quantz-db-rabbitmq-1                 Started 

 ✔ Container quantz-db-redis-access-table-1       Started

MongoDB Client

From other servers

```
mongosh "mongodb://user:pass@192.168.1.7:27017/quantz"
```

```
use quantz
db.user.getIndexes()
```

user

```
db.user.findOne({ _id: ObjectId("66961e8cdb50d5d0004bd6e3") });
```

```
db.user.findOne({ email: "dev1@thinkxinc.com" });
```

```
db.user.findOne({ email: "support@quantz.thinkxinc.com" });
```

user list

```
> db.user.find({}, { email: 1, created: 1, updated: 1, origin: 1 })
```

delete one

```
db.interview.deleteOne({"_id": ObjectId("67189dd60d3c265557a4457b")})
```

```
db.interview.deleteOne({"_id": ObjectId("")})
```

```
db.user.deleteOne({"email": "dev4@thinkxinc.com"})
```

flush

```
db.{collection}.drop()
```

manage db

```
cd /src/quantz-web/web-server
cd system_status

# delete user by email
python manage_db.py --user --email={email} --delete

# get general status
python manage_db.py --general_status --get

# is_signup_restricted=True
python manage_db.py --general_status --is_signup_restricted=true

# add to waiting list
python manage_db.py --general_status --wait_list_emails={email}

# pop {n} from wait list
python manage_db.py --general_status --pop_wait_list={n}
```

ChatData

client_id ff45a50e04ad43ac85a78d01c3d96c8d のChatDataがあるか調べる

```
redis-cli -h 192.168.1.9 -p 6378 -n 0 HGETALL ff45a50e04ad43ac85a78d01c3d96c8d
```

VectorDB

Access / Host

initializing origin data

```
cd /src/quantz-web/web-server/
cd accessdb
python manage_data.py --init
```

flushing host data

```
cd /src/quantz-web/web-server/
cd accessdb
python manage_data.py --flush_hosts
```

flushing usage data

```
cd /src/quantz-web/web-server/
cd accessdb
python manage_data.py --flush_usage
```

flushing access data

```
cd /src/quantz-web/web-server/
cd accessdb
python manage_data.py --flush_access
```

stats host

```
cd /src/quantz-web/web-server/
cd accessdb
. ./stats_host.sh
```

stats access

```
cd /src/quantz-web/web-server/
cd accessdb
. ./stats_access.sh
```

check

```
redis-cli -h 192.168.1.7 -p 6376 -n 0
192.168.1.7:6376> KEYS "host::*"
1) "host::c3456789abcdef1234567890"
2) "host::b23456789abcdef123456789"
3) "host::6761336d842132052346a1bd"
4) "host::a123456789abcdef12345678"

192.168.1.7:6376> GET "host::b23456789abcdef123456789"
"{\"origin\": \"quantz.thinkxinc.com\", \"host_id\": \"b23456789abcdef123456789\", \"monthly_limit\": 9999999999999999, \"start_billing\": \"2024-12-17T07:50:21.977807+00:00\", \"next_billing\": \"2024-12-17T07:50:21.977814+00:00\", \"suspend\": false}"

192.168.1.7:6376> GET "host::6761336d842132052346a1bd"
"{\"origin\": \"quantz.thinkxinc.com\", \"host_id\": \"6761336d842132052346a1bd\", \"monthly_limit\": 9999999999999999, \"start_billing\": \"2025-01-10T02:57:12.669604+00:00\", \"next_billing\": \"2025-01-10T02:57:12.669608+00:00\", \"suspend\": false}"
```

delete host data

```
DEL "host::b23456789abcdef123456789"
```

Crontab (daily_check.py)

setup

```
sudo timedatectl set-timezone UTC
timedatectl
```

```
cd /src/quantz-web/web-server/system_status
chmod +x run_daily_check.sh
```

```
sudo crontab -e

10 15 * * * /src/quantz-web/web-server/system_status/run_daily_check.sh >> /var/log/daily_check.log 2>&1
```

*JST 0時10分

```
sudo touch /var/log/daily_check.log
sudo chmod 666 /var/log/daily_check.log
```

Restart

```
sudo service cron restart
```

List

```
sudo crontab -l
```

Status (if cron is active)

```
sudo service cron status
```

run manually

```
source /src/quantz-web/web-server/venv/bin/activate
sudo -E /src/quantz-web/web-server/venv/bin/python /src/quantz-web/web-server/system_status/daily_check.py --dryrun
```

Local RabbitMQ & Redis Results

setup

```
sudo chmod +x /usr/local/bin/docker-compose
cd /src/quantz-web/vectordb_server
docker-compose up -d
```

status

```
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

Run Celery Worker Process

broker 🌜

```
cd /src/quantz/web-server
cd redis_broker
. ./run.sh
```

celery (billing) 🪐 

```
cd /src/quantz/web-server
cd web_tasks_server
WORKER_TYPE=billing celery -A run:celery_app worker -l info -Q billing.echo,billing.run_payment --hostname=billing_worker_1
```

celery (report) 

```
cd /src/quantz/web-server
cd tasks_server
WORKER_TYPE=report celery -A run:celery_app worker -l info -Q report.echo,report --hostname=report_worker_1
```

Web App Frontend

⭐️ Build

Shorthand

```
cd /src/quantz/web-server/etc
. ./watchsimplicity.sh  # run (1) below
. ./watchapp.sh  # run (2) below
```

build simplicity

```
cd web-server/views/src/ECMA/simplicity
gulp
```

(1) watch simplicity (if needed)

```
cd /src/quantz/
web-server
/views/src/ECMA/simplicity
sudo npx npm-run-all --parallel build:js compile:css
```

(2) Build sources. Copy simplicity. (and watch)

```
cd /src/quantz/web-server/views/
sudo npx npm-run-all --parallel compile:views:js compile:views:css copy:simplicity:js copy:simplicity:css
```

Celery

Check registered tasks

```
cd /src/quantz/web-server
cd tasks_server
celery -A run:celery_app_web inspect registered
```

Inspect

old logs

```
sudo journalctl -u uwsgi.service -n 700
```

Logrotate

```
sudo vim /etc/logrotate.d/rsyslog
```

check conf and restart

```
sudo rsyslogd -N1
sudo systemctl restart rsyslog
```

最新の設定

```
/var/log/syslog
/var/log/mail.info
/var/log/mail.warn
/var/log/mail.err
/var/log/mail.log
/var/log/daemon.log
/var/log/kern.log
/var/log/auth.log
/var/log/user.log
/var/log/lpr.log
/var/log/cron.log
/var/log/debug
/var/log/messages
{
        rotate 7
        daily
        size 100M
        missingok
        notifempty
        compress
        delaycompress
        copytrancate
        sharedscripts
        postrotate
                /usr/lib/rsyslog/rsyslog-rotate
        endscript
}
```

Diskfull Supercom

Others

Delete orphaned entries in vectordb

(delete all materials in vdb not in mongodb)

```
cd /src/quantz-web
python sync_materials.py
```
