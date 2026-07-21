#!/usr/bin/env bash
# thinkx-system/infra/run/build_and_restart.sh
#
# サービスを1つ、配信物をコンパイルしてから再起動し、応答を確かめる。
#
# 「作り直す」ではない。セットアップはやり直さない。やるのは less/js のコンパイルだけ。
#
#   使い方: bash infra/run/build_and_restart.sh <thinkx|transformism|kazukiotsukacom|nginx-web-root|loadbalancer>
#
# コンパイルが要るのは配信物が生成物のサイトだけ(views/css・views/js は .gitignore)。
# ソースを配っただけでは配信に出ないため、restart の前に必ず作り直す。条件分岐で
# 「変わったときだけ」にはしない。判定を誤ると古い配信物を出し続ける(本番で実際に起きた)。
#
# この箱が担当していないサービスは何もせず 0 で返る。web と lb は同じリポジトリを持つため、
# 判定を誤ると「LB の設定変更で web を巻き戻す」「lb で thinkx を起動する」が起きる。
# 判定は「今この箱で現に動いているか」で行う(ユニットの有無では判別できない。
# lb にも uwsgi_thinkx のユニットは存在し inactive で置かれている)。
#
# 応答が 200 でなければ非ゼロで返る。呼び出し側(sync_from_origin.sh)が戻しを判断する。

set -uo pipefail

build_and_restart() {
  local svc="${1:?usage: build_and_restart.sh <service>}"
  local unit port host code owner

  case "$svc" in
    thinkx)          unit=uwsgi_thinkx;          port=8005; host=thinkxinc.com    ;;
    transformism)    unit=uwsgi_transformism;    port=8006; host=transformism.art ;;
    kazukiotsukacom) unit=uwsgi_kazukiotsukacom; port=8007; host=kazukiotsuka.com ;;
    nginx-web-root)  unit=nginx; port=; host=; owner=nginx-web-root ;;
    loadbalancer)    unit=nginx; port=; host=; owner=loadbalancer   ;;
    *) echo "FAIL: 不明なサービス: $svc" >&2; return 1 ;;
  esac

  # この箱で動いていないサービスは担当外
  if ! systemctl is-active "$unit" >/dev/null 2>&1; then
    echo "skip: $svc はこの箱($(hostname))で動いていない"
    return 0
  fi

  # nginx は web と lb の両方で動く。どちらの設定で動いているかを systemd の
  # ユニット実体で見分ける(web -> nginx-web-root / lb -> loadbalancer)。
  if [ "$unit" = nginx ]; then
    case "$(readlink -f /etc/systemd/system/nginx.service 2>/dev/null)" in
      */"${owner}"/*) ;;
      *) echo "skip: この箱($(hostname))の nginx は $owner の設定で動いていない"; return 0 ;;
    esac
  fi

  if [ "$svc" = thinkx ]; then
    echo "== build $svc =="
    cd /src/thinkx/web-server/views || return 1
    sudo -u kaz npx babel src/js --out-dir js || return 1
    sudo -u kaz npx lessc src/less/main.less css/main.css || return 1
    sudo chown -R kaz:serveradmins js css 2>/dev/null
  fi
  # transformism と kazukiotsukacom は js/css の一部が git 追跡されており、ビルドが同じ
  # パスへ書き出すと repo が恒久的に dirty になる恐れがある。追跡物と生成物が一致するか
  # 確認できるまでビルドは通さない(infra/findings.md)。

  echo "== restart $svc ($unit) =="
  systemctl restart "$unit" || return 1
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
