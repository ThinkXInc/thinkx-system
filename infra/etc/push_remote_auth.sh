#!/usr/bin/env bash
# thinkx-system/infra/etc/push_remote_auth.sh   【分類: 変更系(本番 web の .env に書く・uwsgi_thinkx を再起動する)】
#
# KOBITO リモコンの入口 https://thinkxinc.com/remote_control/ の Basic 認証(ユーザー名・パスワード)を
# 本番 web の thinkx の .env(/src/thinkx/.env = thinkx clone ルート。config.py の DOTENV_PATH)に書く。
# 既存の REMOTE_BASIC_AUTH_* 行は置き換える。パスワードは画面に出さず、Mac のシェル履歴にも残さない。
# 手順書: infra/docs/KOBITO_セットアップ手順.md 4
#
#   使い方: bash infra/etc/push_remote_auth.sh supercom-web1
#   (ユーザー名とパスワードを対話で聞く。最後に本番 URL へ認証つきで curl して 200 を確認する)

set -euo pipefail

G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
host="${1:-}"
[ -n "$host" ] || { printf '%b\n' "${Y}ssh の宛先を指定してください。 使い方: bash infra/etc/push_remote_auth.sh supercom-web1${Z}"; exit 1; }

ENV_FILE=/src/thinkx/.env
STRAY_FILE=/src/thinkx/web-server/.env

printf 'ユーザー名(例: kobito): '
read -r user
printf 'パスワード(表示されません): '
read -rs pass
echo
[ -n "$user" ] && [ -n "$pass" ] || { printf '%b\n' "${R}FAIL: ユーザー名かパスワードが空です${Z}"; exit 1; }
case "$user$pass" in *"'"*|*'\'*) printf '%b\n' "${R}FAIL: ' と \\ は使えません${Z}"; exit 1 ;; esac

# 値は引数でなく標準入力で渡す(ps や履歴に出さない)
printf 'REMOTE_BASIC_AUTH_USER=%s\nREMOTE_BASIC_AUTH_PASS=%s\n' "$user" "$pass" | ssh "$host" '
  set -e
  sudo -n install -m 0640 -o kaz -g serveradmins /dev/null /tmp/remote_auth.env
  cat > /tmp/remote_auth.env.new
  sudo -n bash -c "grep -v \"^REMOTE_BASIC_AUTH_\" '"$ENV_FILE"' > /tmp/remote_auth.env; cat /tmp/remote_auth.env.new >> /tmp/remote_auth.env; install -m 0640 -o kaz -g serveradmins /tmp/remote_auth.env '"$ENV_FILE"'; rm -f /tmp/remote_auth.env /tmp/remote_auth.env.new"
  if [ -f '"$STRAY_FILE"' ] && ! sudo -n grep -qv "^REMOTE_BASIC_AUTH_" '"$STRAY_FILE"'; then sudo -n rm -f '"$STRAY_FILE"'; echo "誤って作られた '"$STRAY_FILE"' を削除"; fi
  sudo -n systemctl restart uwsgi_thinkx
  sleep 2
  systemctl is-active uwsgi_thinkx
'

# verify(本番 URL に認証つきで 200・認証なしで 401)
code_ok="$(curl -s -o /dev/null -m 15 -u "$user:$pass" -w '%{http_code}' https://thinkxinc.com/remote_control/ || true)"
code_ng="$(curl -s -o /dev/null -m 15 -w '%{http_code}' https://thinkxinc.com/remote_control/ || true)"
if [ "$code_ok" = 200 ] && [ "$code_ng" = 401 ]; then
  printf '%b\n' "${G}OK: push_remote_auth https://thinkxinc.com/remote_control/ 認証あり=200 / なし=401${Z}"
else
  printf '%b\n' "${R}FAIL: push_remote_auth 認証あり=${code_ok} / なし=${code_ng}(本番に /remote_control/ がまだ出ていないなら 404)${Z}"
  exit 1
fi
