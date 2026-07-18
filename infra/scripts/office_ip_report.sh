#!/usr/bin/env bash
# thinkx-system/infra/scripts/office_ip_report.sh   【分類: 観測系(見るだけ・状態を変えない)】
#
# SSH(22) を許可中の IP ごとに「最終アクセス日時」を報告する。
#   - 許可リスト: prod/staging の SG から実測
#   - 最終アクセス: 4台の auth.log(sshd の Accepted 行)から実測
# 長期間アクセスの無い許可 IP = 撤去候補(黄)。
#
#   使い方: bash infra/scripts/office_ip_report.sh

office_ip_report() {
  local G=$'\033[32m' Y=$'\033[33m' Z=$'\033[0m'
  local allowed hosts h

  echo "── 許可中の IP(SG 実測)──"
  allowed="$(aws ec2 describe-security-groups \
      --filters "Name=group-name,Values=supercom-prod-web-sg,supercom-prod-lb-sg,supercom-staging-web-sg,supercom-staging-lb-sg" \
      --query "SecurityGroups[].IpPermissions[?FromPort==\`22\`].IpRanges[].CidrIp" --output text | tr '\t' '\n' | sort -u)"
  printf '%s\n' "$allowed"
  echo

  echo "── 最終アクセス(4台の auth.log 実測)──"
  hosts="supercom-web1 supercom-lb1 supercom-web1-stg supercom-lb1-stg"
  {
    for h in $hosts; do
      ssh -o BatchMode=yes -o ConnectTimeout=8 "$h" \
        'sudo grep -h "sshd.*Accepted" /var/log/auth.log /var/log/auth.log.1 2>/dev/null' 2>/dev/null \
        | sed "s/^/$h /"
    done
  } | python3 -c '
import sys, re
last = {}
for line in sys.stdin:
    m = re.match(r"(\S+)\s+(\S+)\s+.*?Accepted \S+ for (\S+) from (\S+)", line)
    if not m:
        continue
    host, ts, user, ip = m.groups()
    key = ip
    if key not in last or ts > last[key][0]:
        last[key] = (ts, host, user)
for ip in sorted(last):
    ts, host, user = last[ip]
    print(f"{ip:18s} 最終 {ts}  ({host} / {user})")
if not last:
    print("アクセス記録なし(auth.log に Accepted 行が無い)")
'
  echo

  echo "── 撤去候補(許可されているがアクセス記録の無い IP)──"
  local found=0 cidr ip
  for cidr in $allowed; do
    ip="${cidr%/32}"
    {
      for h in $hosts; do
        ssh -o BatchMode=yes -o ConnectTimeout=8 "$h" \
          "sudo grep -q \"Accepted .* from $ip \" /var/log/auth.log /var/log/auth.log.1 2>/dev/null" 2>/dev/null && echo hit && break
      done
    } | grep -q hit || { printf '%b\n' "${Y}$cidr(アクセス記録なし)${Z}"; found=1; }
  done
  [ "$found" -eq 0 ] && printf '%b\n' "${G}なし(許可 IP はすべて使用実績あり)${Z}"
  printf '%b\n' "${G}OK: office_ip_report 完了${Z}"
}

office_ip_report "$@"
