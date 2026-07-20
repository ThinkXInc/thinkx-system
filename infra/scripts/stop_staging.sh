#!/usr/bin/env bash
# thinkx-system/infra/scripts/stop_staging.sh   【分類: 変更系(staging の EC2 2台を停止する)】
#
# 使わない間の staging を停止して料金を下げる(EC2 の時間課金が止まる。EBS と EIP は課金継続)。
# EIP は台帳(D-53)が保持するため IP は変わらず、再開後も DNS・ssh 設定はそのまま。
# prod は対象にできない(このスクリプトは staging タグ固定)。再開は start_staging.sh。
#
#   使い方: bash infra/scripts/stop_staging.sh

set -euo pipefail

G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'

IDS="$(aws ec2 describe-instances --filters "Name=tag:Env,Values=staging" "Name=tag:Project,Values=supercom" "Name=instance-state-name,Values=running" --query "Reservations[].Instances[].InstanceId" --output text)"
[ -n "$IDS" ] || { printf '%b\n' "${Y}WARN: stop_staging 稼働中の staging インスタンスなし(既に停止済み)${Z}"; exit 0; }

echo "停止対象: $IDS"
aws ec2 stop-instances --instance-ids $IDS --query "StoppingInstances[].[InstanceId,CurrentState.Name]" --output text
aws ec2 wait instance-stopped --instance-ids $IDS

printf '%b\n' "${G}OK: stop_staging staging 2台を停止(IP は保持・再開は start_staging.sh)${Z}"
