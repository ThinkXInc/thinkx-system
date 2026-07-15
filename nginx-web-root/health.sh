#!/usr/bin/env bash
# health.sh 【観測系】web(supercom2)の内部健全性を1画面で表示
#   SSH でログを漁らなくても「uwsgi/Flask が正常起動したか・エラーを吐いていないか」を知るためのもの。
#   サーバー上で実行: bash /src/nginx-web-root/health.sh
#   (bash.md 観測系: set -e/exit 不使用・関数+return)

health_main() {
  local svc code h

  echo "== web health $(date '+%F %T') =="

  echo "-- systemd --"
  for svc in uwsgi_thinkx uwsgi_kazukiotsukacom nginx; do
    printf "  %-22s %s\n" "$svc" "$(systemctl is-active "$svc" 2>/dev/null || true)"
  done

  echo "-- nginx configtest --"
  sudo nginx -t -p /src/nginx-web-root -c /src/nginx-web-root/nginx.conf 2>&1 | tail -1

  echo "-- HTTP(localhost・Host 別)--"
  # *kazukiotsuka: LB が送る実 Host は kazukiotsuka.com。conf の server_name は kazukiotsukacom.com だが
  #  8007 唯一の server のため default で受ける(prod と同一挙動)。server_name を直すならサイト repo 側で
  for h in "thinkxinc.com:8005" "truetechjapan.com:8005" "nntm.thinkxinc.com:8005" "kazukiotsuka.com:8007"; do
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 -H "Host: ${h%%:*}" "http://localhost:${h##*:}/" 2>/dev/null || true)"
    printf "  %-24s -> %s\n" "$h" "${code:-000}"
  done

  echo "-- uwsgi 起動確認(WSGI app ready)--"
  for svc in uwsgi_thinkx uwsgi_kazukiotsukacom; do
    printf "  %-22s %s\n" "$svc" \
      "$(journalctl -u "$svc" -n 500 --no-pager 2>/dev/null | grep -E 'WSGI app .* ready|spawned uWSGI' | tail -1 || true)"
  done

  echo "-- uwsgi 直近エラー(Traceback/Error・各最新3)--"
  for svc in uwsgi_thinkx uwsgi_kazukiotsukacom; do
    echo "  [$svc]"
    journalctl -u "$svc" -n 500 --no-pager 2>/dev/null | grep -E 'Traceback|ERROR|Error|Exception' | tail -3 | sed 's/^/    /'
  done

  echo "-- nginx 直近エラー(最新3)--"
  sudo tail -3 /var/log/nginx/error.log 2>/dev/null | sed 's/^/  /'

  return 0
}

health_main "$@"
