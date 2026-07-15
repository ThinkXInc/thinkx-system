#!/usr/bin/env bash
# etc/trace.sh 【観測系】GIP への 1 リクエストが LB nginx → web nginx → uwsgi のどこまで届いたかを一発判定
#   使い方(Mac から): infra/etc/trace.sh [host]     # 既定 thinkxinc.com
#   一意 ID 付きで curl し、各層のログを ID で grep して ✓/✗ と「止まった層」を表示する。
#   IP は terraform output(EIP)から取得。ssh 鍵は ~/.ssh/supercom.pem。
#   (bash.md 観測系: set -e/exit 不使用・関数+return・cd はサブシェル)

trace_main() {
  local host="${1:-thinkxinc.com}"
  local here tfdir lb webpub id code lbacc weback uw
  here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
  tfdir="$here/../terraform"

  command -v terraform >/dev/null 2>&1 || { echo "terraform が見つからない" >&2; return 0; }
  lb="$(terraform -chdir="$tfdir" output -raw lb_public_ip 2>/dev/null)"
  webpub="$(terraform -chdir="$tfdir" output -raw web_public_ip 2>/dev/null)"
  [ -z "$lb" ] && { echo "terraform output から LB IP を取得できない(apply 済みか確認)" >&2; return 0; }

  local S="ssh -i $HOME/.ssh/supercom.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new"
  id="trace-$(date +%s)-$$"

  echo "== trace: https://${host}/ (LB=${lb} / id=${id}) =="
  code="$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 --resolve "${host}:443:${lb}" "https://${host}/?${id}" 2>/dev/null)"
  sleep 1

  lbacc="$($S "ubuntu@${lb}"     "sudo grep -h '${id}' /var/log/nginx/access.log 2>/dev/null | tail -1" 2>/dev/null)"
  weback="$($S "ubuntu@${webpub}" "sudo grep -h '${id}' /var/log/nginx/access.log 2>/dev/null | tail -1" 2>/dev/null)"
  uw="$($S "ubuntu@${webpub}"     "journalctl -u uwsgi_thinkx -u uwsgi_kazukiotsuka --since '3 min ago' --no-pager 2>/dev/null | grep '${id}' | tail -1" 2>/dev/null)"

  echo
  printf "  %-28s %s\n" "① curl → LB(HTTP code)"   "${code:-000}"
  printf "  %-28s %s\n" "② LB nginx access.log"     "$([ -n "$lbacc" ]  && echo '✓ 記録あり' || echo '✗ なし')"
  printf "  %-28s %s\n" "③ web nginx access.log"    "$([ -n "$weback" ] && echo '✓ 記録あり' || echo '✗ なし')"
  printf "  %-28s %s\n" "④ uwsgi(journal)"          "$([ -n "$uw" ]     && echo '✓ 記録あり' || echo '✗ なし')"
  echo

  if [ "${code:-000}" = "000" ]; then
    echo "▶ 判定: LB に到達していない(DNS/SG 443/LB nginx 停止のいずれか)"
    $S "ubuntu@${lb}" "systemctl is-active nginx; sudo tail -3 /var/log/nginx/error.log 2>/dev/null" 2>/dev/null | sed 's/^/  lb: /'
  elif [ -z "$lbacc" ]; then
    echo "▶ 判定: LB nginx がリクエストを記録していない(access_log 設定 or 別 server ブロックへ)"
  elif [ -z "$weback" ]; then
    echo "▶ 判定: LB → web で止まっている(proxy_pass 向き先 IP / SG 8000-8009 / web nginx 停止)"
    $S "ubuntu@${lb}" "sudo tail -3 /var/log/nginx/error.log 2>/dev/null" 2>/dev/null | sed 's/^/  lb-err: /'
  elif [ -z "$uw" ]; then
    echo "▶ 判定: web nginx → uwsgi で止まっている(socket 不在 / uwsgi 停止 / アプリ起動失敗)"
    $S "ubuntu@${webpub}" "bash /src/nginx-web-root/health.sh" 2>/dev/null | sed 's/^/  /'
  else
    echo "▶ 判定: 全層到達(HTTP ${code})。アプリ内エラーの有無は health.sh の uwsgi エラー欄を参照"
  fi

  return 0
}

trace_main "$@"
