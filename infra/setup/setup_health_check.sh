#!/usr/bin/env bash
# thinkx-system/infra/setup/setup_health_check.sh 【分類: 変更系(LB に health check の timer を入れる)】
#
#   使い方: ssh supercom-lb1 'sudo bash -s' < infra/setup/setup_health_check.sh
#
# 前提: /src/thinkx-system(production checkout)に infra/scripts/health_check.sh がある。
# 実行後に /etc/supercom-health.env へ DISCORD_WEBHOOK_URL と SITES を書く
# (中身と手順は infra/runbooks/health-check.md)。env が空の間は通知せず標準出力に出るだけ。

set -euo pipefail

mkdir -p /var/lib/supercom-health

touch /etc/supercom-health.env
chmod 600 /etc/supercom-health.env

cat > /etc/systemd/system/health-check.service <<'UNIT'
[Unit]
Description=site health check -> Discord (thinkx-system)

[Service]
Type=oneshot
Environment=HEALTH_ENV=/etc/supercom-health.env
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
