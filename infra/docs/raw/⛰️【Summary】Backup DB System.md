# ⛰️【Summary】Backup DB System

_created: 20240602T045519Z / updated: 20241217T055838Z_

Log

```
sudo tail -f /var/log/backup.log | ccze -A
```

Restart

```
sudo service cron restart
```

Status (if cron is active)

```
sudo service cron status
```

Run manually

```
sudo /src/quantz-db/backup_system/venv/bin/python backup.py
```

Edit crontab

```
sudo crontab -e
```

*Celery trouble shooting (celery is not used anymore)

check if task is registerd

```
cd /src/quantz-db/backup_system
celery -A backup inspect registered
```

call manually

```
cd /src/quantz-db/backup_system
celery -A backup call backup.backup_database
```

run directly

```
cd /src/quantz-db/backup_system
python backup.py -t # run immediately
```

Set up db server for backup

```
ssh supercom3c
```

make serveradmins goup

```
sudo groupadd serveradmins
sudo usermod -a -G serveradmins kaz
```

make backup directory

```
sudo mkdir -p /backup
sudo chown kaz:serveradmins /backup
sudo chmod 770 /backup
```

Set up scheduler by crontab

```
sudo timedatectl set-timezone UTC
```

```
timedatectl
```

(default)

               Local time: 月 2024-06-03 12:25:50 JST

           Universal time: 月 2024-06-03 03:25:50 UTC

                 RTC time: 月 2024-06-03 03:25:50

                Time zone: Asia/Tokyo (JST, +0900)

System clock synchronized: yes

              NTP service: active

          RTC in local TZ: no

(updated)

               Local time: 月 2024-06-03 03:26:04 UTC

           Universal time: 月 2024-06-03 03:26:04 UTC

                 RTC time: 月 2024-06-03 03:26:04

                Time zone: UTC (UTC, +0000)

System clock synchronized: yes

              NTP service: active

          RTC in local TZ: no

```
cd /src/quantz-db/backup_system
chmod +x run_backup.sh
```

```
sudo crontab -e

0 15 * * * /src/quantz-db/backup_system/run_backup.sh >> /var/log/backup.log 2>&1
```

-> 本来UTC時刻なら 0 15 でJST 0:00 になるはずだがなぜか0 15だと日本時間15時に起動してしまうので0 0 にしている (FIXME)

-> その後しばらくして9時に届くようになったので0 15に変更した

```
$ sudo crontab -l
```

0 0 * * * /src/quantz-db/backup_system/run_backup.sh >> /var/log/backup.log 2>&1

Set up log file

```
sudo touch /var/log/backup.log
sudo chmod 666 /var/log/backup.log
```

SSH KEY *not used

make serveradmins key

```
sudo mkdir -p /etc/ssh/serveradmins_keys
sudo chown root:serveradmins /etc/ssh/serveradmins_keys
sudo chmod 770 /etc/ssh/serveradmins_keys
```

make the key for ssh login to the backup server

```
cd /etc/ssh/serveradmins_keys
ssh-keygen -t rsa -b 4096 -C "backup@dbserver"
```

Generating public/private rsa key pair.

Enter file in which to save the key (/home/kaz/.ssh/id_rsa): backup_rsa

Enter passphrase (empty for no passphrase):

Enter same passphrase again:

Your identification has been saved in backup_rsa

Your public key has been saved in backup_rsa.pub

The key fingerprint is:

SHA256:C6iKG1umd4VZXPO+DxfBEPTJ7FOikPIqc4uUIL9w1T0 backup@dbserver

The key's randomart image is:

+---[RSA 4096]----+

|         .+.     |

|        o. * .   |

|     ...oo  O .  |

|     oo+ ..o +   |

|. . o+o E.. +    |

| o +o..o o.  o   |

|o * =.o . ...    |

|.X.o.= .  .o     |

|*o... .    ..    |

+----[SHA256]-----+

set ssh key permissions

```
sudo chmod 660 /etc/ssh/serveradmins_keys/backup_rsa
sudo chmod 644 /etc/ssh/serveradmins_keys/backup_rsa.pub
```
