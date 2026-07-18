#!/usr/bin/env bash
# thinkx-system/infra/scripts/office_ip_report.sh   【分類: 観測系(見るだけ・状態を変えない)】
#
# SSH(22) の許可状態を棚卸しする。
#   - SG ごとの許可元 CIDR: AWS から実測(supercom 管理外の SG も列挙、0.0.0.0/0 は赤)
#   - 最終アクセス: 4台の auth.log(sshd の Accepted 行)から IP ごとに実測
#   - supercom SG で許可されているのにアクセス記録が無い IP = 撤去候補(黄)
#
#   使い方: bash infra/scripts/office_ip_report.sh

office_ip_report() {
  local G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
  local sgjson accepted allowed hosts h

  sgjson="$(aws ec2 describe-security-groups --output json)"
  [ -n "$sgjson" ] || { printf '%b\n' "${R}FAIL: office_ip_report describe-security-groups が空(aws 認証を確認)${Z}"; return 1; }

  echo "── SSH(22) を許可している SG と許可元(AWS 実測)──"
  printf '%s' "$sgjson" | python3 -c '
import sys, json
RED, Z = "\033[31m", "\033[0m"
for sg in json.load(sys.stdin)["SecurityGroups"]:
    name = sg["GroupName"]
    cidrs = [r["CidrIp"] for p in sg["IpPermissions"] if p.get("FromPort") == 22 for r in p.get("IpRanges", [])]
    for c in sorted(set(cidrs)):
        line = f"{c:20s} {name}"
        print(f"{RED}{line}  <- 全世界に開放{Z}" if c == "0.0.0.0/0" else line)
'
  echo

  echo "── 最終アクセス(4台の auth.log 実測)──"
  hosts="supercom-web1 supercom-lb1 supercom-web1-stg supercom-lb1-stg"
  accepted="$(for h in $hosts; do
    ssh -o BatchMode=yes -o ConnectTimeout=8 "$h" \
      'sudo grep -h "sshd.*Accepted" /var/log/auth.log /var/log/auth.log.1 2>/dev/null' 2>/dev/null \
      | sed "s/^/$h /"
  done)"
  printf '%s\n' "$accepted" | python3 -c '
import sys, re
from datetime import datetime
now = datetime.now()
last = {}
for line in sys.stdin:
    m = re.match(r"(\S+)\s+(\w{3})\s+(\d+)\s+([\d:]+)\s+.*?Accepted \S+ for (\S+) from ([\d.]+)", line)
    if not m:
        continue
    host, mon, day, hms, user, ip = m.groups()
    try:
        ts = datetime.strptime(f"{mon} {day} {hms} {now.year}", "%b %d %H:%M:%S %Y")
    except ValueError:
        continue
    if ts > now:
        ts = ts.replace(year=now.year - 1)
    if ip not in last or ts > last[ip][0]:
        last[ip] = (ts, host, user)
for ip, (ts, host, user) in sorted(last.items()):
    print(f"{ip:18s} 最終 {ts:%Y-%m-%d %H:%M:%S}  ({host} / {user})")
if not last:
    print("アクセス記録なし(auth.log に Accepted 行が無い)")
'
  echo

  echo "── 撤去候補(supercom SG で許可されているがアクセス記録の無い IP)──"
  allowed="$(printf '%s' "$sgjson" | python3 -c '
import sys, json
for sg in json.load(sys.stdin)["SecurityGroups"]:
    if not sg["GroupName"].startswith("supercom-"):
        continue
    for p in sg["IpPermissions"]:
        if p.get("FromPort") == 22:
            for r in p.get("IpRanges", []):
                print(r["CidrIp"])
' | sort -u)"
  local found=0 cidr ip
  for cidr in $allowed; do
    ip="${cidr%/32}"
    printf '%s\n' "$accepted" | grep -q "from $ip " || { printf '%b\n' "${Y}$cidr(アクセス記録なし)${Z}"; found=1; }
  done
  [ "$found" -eq 0 ] && printf '%b\n' "${G}なし(supercom SG の許可 IP はすべて使用実績あり)${Z}"
  printf '%b\n' "${G}OK: office_ip_report 完了${Z}"
}

office_ip_report "$@"
