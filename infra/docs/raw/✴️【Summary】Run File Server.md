# ✴️【Summary】Run File Server

_created: 20241106T075738Z / updated: 20241116T091128Z_

Log

```
sudo journalctl -fu fileserver.service --output cat -n 2000
```

Restart

```
cd /src/quantz-web/fileserver
cd service
. ./restart.sh fileserver
```

Manually run

```
cd /src/quantz-web/fileserver
go run fileserver.go
```

client

```
cd /src/quantz-web/fileserver
go run testclient.go
```

```
/disk1/quantz$ tree
.
└── test_service
    └── 2024
        └── 11
            └── 06
                └── test_identifier
                    ├── Speaker1_0.jpeg
                    ├── Speaker1_0.mp4
                    ├── all.webm
                    ├── all_compressed.mp4
                    └── metadata.json
```

https://quantz.thinkxinc.com/fs/files/test_service/2024/11/06/test_identifier/metadata.json

Inspection

/fs/files/によるリクスト

fileserverのログに何も出ない

-> 到達していないか 
http.Handle(config.Cfg.AccessURL, http.StripPrefix(config.Cfg.AccessURL, fs))

で受け付けるパスのルールにないか

-> 到達していればproxyのaccess logでは404になる そうでなければ502になる

-> 404の場合はパスのルールを疑う proxyの `

```
proxy_pass http://$files_quantz;
```

の最後が\があると受け付けない

Setup Daemon

/src/quantz-web/fileserver/service/fileserver.service

```
cd /src/quantz-web/fileserver/service
```

```
sudo ln -s /src/quantz-web/fileserver/service/fileserver.service /etc/systemd/system/fileserver.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable fileserver.service
sudo systemctl start fileserver.service
```

```
sudo journalctl -fu fileserver.service --output cat
```

*8080 already use

```
sudo netstat -tulnp | grep 8080
sudo kill {ps number}
```

Crontab (daily_check.py)

setup

```
sudo timedatectl set-timezone UTC
timedatectl
```

               Local time: 木 2024-11-14 02:00:27 UTC

           Universal time: 木 2024-11-14 02:00:27 UTC

                 RTC time: 木 2024-11-14 02:00:28

                Time zone: UTC (UTC, +0000)

System clock synchronized: yes

              NTP service: active

          RTC in local TZ: no

```
cd /src/quantz-web/fileserver
chmod +x run_retry.sh
```

```
sudo crontab -e

*/10 * * * * /src/quantz-web/fileserver/run_retry.sh >> /var/log/fileserver_retry.log 2>&1
```

*JST 0時10分

```
sudo touch /var/log/fileserver_retry.log
sudo chmod 666 /var/log/fileserver_retry.log
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

Log

```
tail -f /var/log/fileserver_retry.log
```

Logrotate

```
sudo vim /etc/logrotate.d/rsyslog
```

check conf

```
sudo rsyslogd -N1
```

restart

```
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
