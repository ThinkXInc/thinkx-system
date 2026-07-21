#!/usr/bin/env bash
# thinkx-system/infra/run/build_and_restart.sh
#
# サービスを1つ、作り直して再起動し、応答を確かめる。
#
#   使い方: bash infra/run/build_and_restart.sh <thinkx|transformism|kazukiotsukacom|nginx-web-root|loadbalancer>
#
# ビルドが要るのは配信物が生成物のサイトだけ(views/css・views/js は .gitignore)。
# ソースを配っただけでは配信に出ないため、restart の前に必ず作り直す。条件分岐で
# 「変わったときだけ」にはしない。判定を誤ると古い配信物を出し続ける(本番で実際に起きた)。
#
# 応答が 200 でなければ非ゼロで返る。呼び出し側(sync_from_origin.sh)が戻しを判断する。

set -uo pipefail

build_and_restart() {
  local svc="${1:?usage: build_and_restart.sh <service>}"
  local unit port host code

  case "$svc" in
    thinkx)
      unit=uwsgi_thinkx; port=8005; host=thinkxinc.com
      echo "== build $svc =="
      cd /src/thinkx/web-server/views || return 1
      sudo -u kaz npx babel src/js --out-dir js
      sudo -u kaz npx lessc src/less/main.less css/main.css
      sudo chown -R kaz:serveradmins js css 2>/dev/null
      ;;
    # transformism と kazukiotsukacom は js/css の一部が git 追跡されており、
    # ビルドが同じパスへ書き出すと repo が恒久的に dirty になる恐れがある。
    # 追跡物と生成物が一致するか確認できるまでビルドは通さない(infra/findings.md)。
    transformism)    unit=uwsgi_transformism;    port=8006; host=transformism.art ;;
    kazukiotsukacom) unit=uwsgi_kazukiotsukacom; port=8007; host=kazukiotsuka.com ;;
    nginx-web-root)  unit=nginx; port=; host= ;;
    loadbalancer)    unit=nginx; port=; host= ;;
    *) echo "FAIL: 不明なサービス: $svc" >&2; return 1 ;;
  esac

  echo "== restart $svc ($unit) =="
  systemctl restart "$unit" || systemctl restart "$unit.service" || return 1
  sleep 2

  if [ -n "$port" ]; then
    code="$(curl -s -o /dev/null -w '%{http_code}' -m 10 -H "Host: $host" "http://localhost:$port/" || true)"
  else
    code="$(systemctl is-active "$unit" >/dev/null 2>&1 && echo 200 || echo 000)"
  fi

  if [ "$code" = 200 ]; then
    printf '\033[32mOK: %s -> %s\033[0m\n' "$svc" "$code"
    return 0
  fi
  printf '\033[31mFAIL: %s -> %s\033[0m\n' "$svc" "$code"
  return 1
}

build_and_restart "$@"
