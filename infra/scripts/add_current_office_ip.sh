#!/usr/bin/env bash
# thinkx-system/infra/scripts/add_current_office_ip.sh   【分類: 変更系(SG と tfvars を書き換える)】
#
# ルーターの動的 IP が変わって SSH(22) が締め出されたとき、現在の IP を許可し直す。
#   - prod: terraform.tfvars の my_office_ip を書き換え → terraform apply(承認プロンプトで yes)
#   - staging: SG の 22 番ルールを aws CLI で入れ替え(state は旧 infra リポジトリ管轄のため直接)
#
#   使い方: bash infra/scripts/add_current_office_ip.sh

set -euo pipefail

G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
TF="$HERE/../terraform"

IP="$(curl -s --max-time 10 https://checkip.amazonaws.com)"
[ -n "$IP" ] || { printf '%b\n' "${R}FAIL: add_current_office_ip 現在の IP を取得できない${Z}"; exit 1; }
printf '現在の IP: %s\n' "$IP"

# prod: tfvars のリストに現在 IP を追記して terraform apply(SG は in-place 更新)
# (旧単数形 my_office_ip が残っていればリスト形式へ自動移行)
sed -i.bak 's|^my_office_ip = "\(.*\)"|my_office_ips = ["\1"]|' "$TF/terraform.tfvars"
if grep -q "\"$IP/32\"" "$TF/terraform.tfvars"; then
  printf '%s は既に許可リストにある\n' "$IP/32"
else
  sed -i.bak "/^my_office_ips/s|\]|, \"$IP/32\"]|" "$TF/terraform.tfvars"
  printf '# %s を追加 %s\n' "$IP/32" "$(date +%F)" >> "$TF/terraform.tfvars"
fi
grep "^my_office_ips" "$TF/terraform.tfvars"
terraform -chdir="$TF" apply -var="env=prod"

# staging: SG の 22 番に現在 IP を追加(既存の許可は残す)
for sg in supercom-staging-web-sg supercom-staging-lb-sg; do
  gid="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$sg" --query "SecurityGroups[0].GroupId" --output text)"
  aws ec2 authorize-security-group-ingress --group-id "$gid" --protocol tcp --port 22 --cidr "$IP/32" > /dev/null 2>&1 || true
  printf '%s: %s/32 を許可\n' "$sg" "$IP"
done

# verify(4台へ SSH 到達確認。末尾に色で成否)
fail=0
for h in supercom-web1 supercom-lb1 supercom-web1-stg supercom-lb1-stg; do
  if ssh -o BatchMode=yes -o ConnectTimeout=8 "$h" true 2>/dev/null; then
    printf '%b\n' "${G}ok  $h${Z}"
  else
    printf '%b\n' "${R}NG  $h${Z}"; fail=$((fail+1))
  fi
done
if [ "$fail" -eq 0 ]; then
  printf '%b\n' "${G}OK: add_current_office_ip 4台とも SSH 到達($IP/32)${Z}"
else
  printf '%b\n' "${R}FAIL: add_current_office_ip SSH 不達 $fail 台${Z}"
  exit 1
fi
