#!/usr/bin/env bash
# thinkx-system/infra/scripts/start_staging.sh   【分類: 変更系(staging の EC2 2台を起動する)】
#
# stop_staging.sh で停止した staging を再開する。EIP 保持(D-53)のため IP・DNS・ssh 設定は不変。
# サービス(nginx / uwsgi_* / filedrop)は systemd enable 済みのため起動時に自動で立ち上がる。
#
#   使い方: bash infra/scripts/start_staging.sh

set -euo pipefail

G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'

IDS="$(aws ec2 describe-instances --filters "Name=tag:Env,Values=staging" "Name=tag:Project,Values=supercom" "Name=instance-state-name,Values=stopped" --query "Reservations[].Instances[].InstanceId" --output text)"
[ -n "$IDS" ] || { printf '%b\n' "${Y}WARN: start_staging 停止中の staging インスタンスなし(既に稼働中)${Z}"; exit 0; }

echo "起動対象: $IDS"
aws ec2 start-instances --instance-ids $IDS --query "StartingInstances[].[InstanceId,CurrentState.Name]" --output text
aws ec2 wait instance-running --instance-ids $IDS

echo "ssh 到達と主要サービスを確認中(最大 120 秒)..."
OK=""
for i in $(seq 1 24); do
  ssh -o BatchMode=yes -o ConnectTimeout=5 supercom-web1-stg 'systemctl is-active --quiet nginx && systemctl is-active --quiet uwsgi_thinkx' 2>/dev/null && OK=1 && break
  sleep 5
done
[ -n "$OK" ] && printf '%b\n' "${G}OK: start_staging staging 2台が稼働(web の nginx / uwsgi_thinkx も active)${Z}" \
             || printf '%b\n' "${R}FAIL: start_staging インスタンスは running だが web のサービス確認が 120 秒で取れず。check_request_path.sh で追試を${Z}"
