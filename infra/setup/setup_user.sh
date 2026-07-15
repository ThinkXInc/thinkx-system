# user setup for webserver
#
# prerequisites: (none)
#
# *マシンごと 1 回。Deploy key は repo ごとに check_deploykey.py(setup の前に独立実行)で確保する

# group
sudo groupadd -f serveradmins

# user
sudo useradd -m -s /bin/bash -G serveradmins kaz

# ssh config skeleton  (Host 実体は config.d/ に置く。上書き=冪等)
sudo -u kaz -H mkdir -p /home/kaz/.ssh/config.d
sudo -u kaz -H chmod 700 /home/kaz/.ssh /home/kaz/.ssh/config.d
sudo -u kaz -H tee /home/kaz/.ssh/config > /dev/null <<'EOF'
Include config.d/*
EOF
sudo -u kaz chmod 600 /home/kaz/.ssh/config
