#!/usr/bin/env bash
# thinkx-system/infra/setup/setup_health_check.sh 【分類: 変更系(LB に health check の timer を入れる)】
#
#   使い方: ssh supercom-lb1 'sudo bash -s' < infra/setup/setup_health_check.sh
#
# 前提: /src/thinkx-system(production checkout)に infra/scripts/health_check.sh がある。
# 設定はリポジトリ内 infra/health_check/loadbalancer.yaml が正。実行後に /src/loadbalancer/.env へ
# HEALTH_DISCORD_WEBHOOK_URL=... の行を書く(手順は infra/runbooks/health-check.md)。
# 書くまでは通知せず標準出力に出るだけ。

set -euo pipefail

mkdir -p /var/lib/supercom-health

touch /src/loadbalancer/.env
chmod 600 /src/loadbalancer/.env

cat > /etc/systemd/system/health-check.service <<'UNIT'
[Unit]
Description=site health check -> Discord (thinkx-system)

[Service]
Type=oneshot
Environment=HEALTH_CONFIG=/src/thinkx-system/infra/health_check/loadbalancer.yaml
ExecStart=/usr/bin/bash /src/thinkx-system/infra/scripts/health_check.sh
UNIT

cat > /etc/systemd/system/health-check.timer <<'UNIT'
[Unit]
Description=run health check every minute

[Timer]
OnBootSec=60
OnUnitActiveSec=60
AccuracySec=10

[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now health-check.timer
systemctl list-timers health-check.timer --no-pager
