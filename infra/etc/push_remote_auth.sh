#!/usr/bin/env bash
# thinkx-system/infra/etc/push_remote_auth.sh   【分類: 変更系(本番 web の .env に書く・uwsgi_thinkx を再起動する)】
#
# KOBITO リモコンの入口 https://thinkxinc.com/remote_control/ の Basic 認証(ユーザー名・パスワード)を
# 本番 web の thinkx の .env(/src/thinkx/.env = thinkx clone ルート。config.py の DOTENV_PATH)に書く。
# 既存の REMOTE_BASIC_AUTH_* 行は置き換える。パスワードは画面に出さず、Mac のシェル履歴にも残さない。
# 手順書: infra/docs/KOBITO_セットアップ手順.md 4
#
# 書き換えはサーバー側で root の python が「読む → 差し替える → 同じ所有者・権限で原子的に置く」の 1 手で行う。
# /tmp の中間ファイルは使わない(Ubuntu 22.04 の fs.protected_regular=2 で root でも他人の /tmp ファイルに書けず、
# 空ファイルで .env を置き換えて本番を 10 分止めた・2026-09-17)。元の内容が 1 行でも欠けたら書かずに止まる。
#
#   使い方: bash infra/etc/push_remote_auth.sh supercom-web1
#   (ユーザー名とパスワードを対話で聞く。最後に本番 URL へ認証つきで curl して 200 を確認する)

set -euo pipefail

G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
host="${1:-}"
[ -n "$host" ] || { printf '%b\n' "${Y}ssh の宛先を指定してください。 使い方: bash infra/etc/push_remote_auth.sh supercom-web1${Z}"; exit 1; }

ENV_FILE=/src/thinkx/.env

printf 'ユーザー名(例: kobito): '
read -r user
printf 'パスワード(表示されません): '
read -rs pass
echo
[ -n "$user" ] && [ -n "$pass" ] || { printf '%b\n' "${R}FAIL: ユーザー名かパスワードが空です${Z}"; exit 1; }
case "$user$pass" in *[\'\"\\\$]*|*' '*) printf '%b\n' "${R}FAIL: 空白と ' \" \\ \$ は使えません${Z}"; exit 1 ;; esac

# 差し替えのプログラム(サーバー側で root の python が実行)。値は引数でなく標準入力で渡す(ps や履歴に出さない)。
# プログラムは base64 で引数に載せ、標準入力はユーザー名とパスワードだけにする(python3 - だと標準入力を
# プログラムが食ってしまい値が渡らない・2026-09-17 実測)
writer='
import os, stat, sys, tempfile
env_file = sys.argv[1]
user, password = sys.stdin.read().split("\n")[:2]
if not user or not password:
    raise SystemExit("empty user/password")
with open(env_file, "r", encoding="utf-8") as f:
    original = f.read().splitlines()
if not original:
    raise SystemExit(f"{env_file} が空。配布元(Mac の thinkx/.env)から push_env.sh で復元してから実行する")
kept = [line for line in original if not line.startswith("REMOTE_BASIC_AUTH_")]
new_lines = kept + [f"REMOTE_BASIC_AUTH_USER={user}", f"REMOTE_BASIC_AUTH_PASS={password}"]
st = os.stat(env_file)
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(env_file), prefix=".env.")
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")
os.chown(tmp, st.st_uid, st.st_gid)
os.chmod(tmp, stat.S_IMODE(st.st_mode))
os.replace(tmp, env_file)
print(f"{env_file}: {len(kept)} 行を保持 + REMOTE_BASIC_AUTH_* 2 行")
'
writer_b64="$(printf '%s' "$writer" | base64 | tr -d '\n')"
printf '%s\n%s\n' "$user" "$pass" | ssh "$host" "sudo -n python3 -c \"\$(echo $writer_b64 | base64 -d)\" '$ENV_FILE'" \
  || { printf '%b\n' "${R}FAIL: push_remote_auth .env の書き換えに失敗(何も変えていない)${Z}"; exit 1; }

ssh "$host" 'sudo -n systemctl restart uwsgi_thinkx && sleep 3 && systemctl is-active uwsgi_thinkx'

# verify(本番 URL に認証つきで 200・認証なしで 401・トップが 200)
code_ok="$(curl -s -o /dev/null -m 15 -u "$user:$pass" -w '%{http_code}' https://thinkxinc.com/remote_control/ || true)"
code_ng="$(curl -s -o /dev/null -m 15 -w '%{http_code}' https://thinkxinc.com/remote_control/ || true)"
code_top="$(curl -s -o /dev/null -m 15 -w '%{http_code}' https://thinkxinc.com/ || true)"
if [ "$code_ok" = 200 ] && [ "$code_ng" = 401 ] && [ "$code_top" = 200 ]; then
  printf '%b\n' "${G}OK: push_remote_auth https://thinkxinc.com/remote_control/ 認証あり=200 / なし=401 / トップ=200${Z}"
else
  printf '%b\n' "${R}FAIL: push_remote_auth 認証あり=${code_ok} / なし=${code_ng} / トップ=${code_top}${Z}"
  exit 1
fi
