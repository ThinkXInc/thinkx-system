#!/usr/bin/env bash
# thinkx-system/infra/scripts/check_request_path.sh   【分類: 観測系(見るだけ・状態を変えない)】
#
# リクエストの通り道を上流から1ホップずつ疎通確認する(受け入れ試験の前段)。
#   [1] Mac → LB public IP(443 応答)
#   [2] LB の nginx が正しい設定(/src/loadbalancer)で稼働
#   [3] LB → web の内部経路(web1.supercom.internal の DNS 解決と 8005/6/7 への TCP)
#   [4] web の nginx が正しい設定(nginx-web-root)で 8005/6/7 を listen
#   [5] web の uwsgi(Flask)が3サイト分稼働(unix socket + service)
#   [6] web 上で nginx→uwsgi→Flask が 200 を返す
#   [7] Mac → LB → web → Flask の end-to-end https が 200
#
#   使い方: bash infra/scripts/check_request_path.sh <LB_IP> <WEB_alias> <LB_alias>
#   例:     bash infra/scripts/check_request_path.sh 52.197.179.70 supercom-web1 supercom-lb1

check_request_path() {
  local lb_ip="${1:-}" web="${2:-}" lb="${3:-}"
  local G=$'\033[32m' R=$'\033[31m' Z=$'\033[0m'
  local fail=0 code out h p s
  [ -n "$lb_ip" ] && [ -n "$web" ] && [ -n "$lb" ] || {
    printf '%b\n' "${R}FAIL: check_request_path usage: check_request_path.sh <LB_IP> <WEB_alias> <LB_alias>${Z}"; return 1; }

  ok() { printf '%b\n' "${G}ok  [$1] $2${Z}"; }
  ng() { printf '%b\n' "${R}NG  [$1] $2${Z}"; fail=$((fail+1)); }

  # [1] Mac → LB public IP  (TCP 到達で判定。vhost 方式のため IP 直打ちの HTTP 応答は仕様外 —
  #     default server が F13 の残骸に落ち、prod=502 / staging=タイムアウトと環境で症状が変わる)
  code=$(python3 -c 'import socket,sys; s=socket.socket(); s.settimeout(5); s.connect((sys.argv[1],443)); print("ok")' "$lb_ip" 2>/dev/null)
  [ "$code" = "ok" ] && ok 1 "LB public IP $lb_ip の 443 に TCP 到達" \
                     || ng 1 "LB public IP $lb_ip の 443 に届かない"

  # [2] LB nginx(正しい設定で稼働)
  out=$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$lb" \
        'systemctl is-active nginx; sudo cat /proc/$(cat /run/nginx.pid)/cmdline 2>/dev/null | tr "\0" " "' 2>/dev/null)
  echo "$out" | grep -q "^active" && echo "$out" | grep -q "/src/loadbalancer" \
    && ok 2 "LB nginx が /src/loadbalancer 設定で稼働" \
    || ng 2 "LB nginx が不稼働か旧設定(実測: $(echo $out | head -c 80))"

  # [3] LB → web 内部経路(DNS と TCP 8005/6/7)
  out=$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$lb" \
        'getent hosts web1.supercom.internal; for p in 8005 8006 8007; do timeout 3 bash -c "echo > /dev/tcp/web1.supercom.internal/$p" 2>/dev/null && echo "tcp$p ok"; done' 2>/dev/null)
  echo "$out" | grep -q "web1.supercom.internal" \
    && ok 3a "LB で web1.supercom.internal が解決($(echo "$out" | head -1 | awk '{print $1}'))" \
    || ng 3a "LB で web1.supercom.internal が解決できない"
  for p in 8005 8006 8007; do
    echo "$out" | grep -q "tcp$p ok" && ok 3b "LB → web:$p へ TCP 到達" || ng 3b "LB → web:$p へ TCP 不達"
  done

  # [4] web nginx(正しい設定で 8005/6/7 listen)
  out=$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$web" \
        'sudo cat /proc/$(cat /run/nginx.pid)/cmdline 2>/dev/null | tr "\0" " "; sudo ss -ltn' 2>/dev/null)
  echo "$out" | grep -q "nginx-web-root" \
    && ok 4a "web nginx が nginx-web-root 設定で稼働" \
    || ng 4a "web nginx が不稼働か旧設定"
  for p in 8005 8006 8007; do
    echo "$out" | grep -qE ":$p\b" && ok 4b "web nginx が :$p を listen" || ng 4b "web nginx が :$p を listen していない"
  done

  # [5] uwsgi(Flask)3サイト
  out=$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$web" \
        'systemctl is-active uwsgi_thinkx uwsgi_kazukiotsukacom uwsgi_transformism | tr "\n" " "; ls /tmp/uwsgi_*.sock 2>/dev/null' 2>/dev/null)
  for s in thinkx kazukiotsukacom transformism; do
    echo "$out" | grep -q "/tmp/uwsgi_$s.sock" && ok 5 "uwsgi_$s socket あり" || ng 5 "uwsgi_$s socket なし"
  done
  echo "$out" | grep -qE "^active active active" && ok 5 "uwsgi 3サービス active" || ng 5 "uwsgi サービスに不稼働あり($(echo $out | awk '{print $1,$2,$3}'))"

  # [6] web 上で nginx→uwsgi→Flask(localhost 200)
  out=$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$web" \
        'for hp in "thinkxinc.com 8005" "transformism.art 8006" "kazukiotsuka.com 8007"; do set -- $hp; printf "%s=%s " "$2" "$(curl -s -o /dev/null --max-time 8 -w "%{http_code}" -H "Host: $1" http://localhost:$2/)"; done' 2>/dev/null)
  for p in 8005 8006 8007; do
    echo "$out" | grep -q "$p=200" && ok 6 "web 内 :$p → Flask が 200" || ng 6 "web 内 :$p → Flask が 200 以外($(echo $out))"
  done

  # [7] end-to-end(Mac → LB → web → Flask)
  for hd in "thinkxinc.com" "transformism.art" "kazukiotsuka.com"; do
    code=$(curl -sk -o /dev/null --max-time 15 --resolve "$hd:443:$lb_ip" -w '%{http_code}' "https://$hd/")
    [ "$code" = "200" ] && ok 7 "https://$hd/ → 200(end-to-end)" || ng 7 "https://$hd/ → $code"
  done

  echo
  if [ "$fail" -eq 0 ]; then
    printf '%b\n' "${G}OK: check_request_path 全ホップ green${Z}"
  else
    printf '%b\n' "${R}FAIL: check_request_path 不通 $fail 箇所(最初の NG が詰まっている場所)${Z}"
  fi
  return "$fail"
}

check_request_path "$@"
