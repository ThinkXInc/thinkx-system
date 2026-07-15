#!/usr/bin/env bash
# etc/push_secrets.sh — secrets(certs / deploykeys / env)+ check_deploykey.py を host の /tmp へ送る
#   Mac から、EC2 が立っていればいつでも: infra/etc/push_secrets.sh supercom-web
#   真実は infra/{certs,deploykeys,env}/(.gitignore)。terraform(箱作り)とは独立に何度でも実行できる。

push_secrets() {
  local host="${1:?usage: push_secrets.sh <ssh-host>}"
  local here infra
  here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
  infra="$(cd "$here/.." && pwd)"

  # COPYFILE_DISABLE: Mac 拡張属性を除く
  COPYFILE_DISABLE=1 tar czf /tmp/secrets.tgz -C "$infra" certs deploykeys || return 1
  scp /tmp/secrets.tgz "$infra/setup/check_deploykey.py" "$host:/tmp/" || return 1
  echo "pushed: secrets.tgz + check_deploykey.py -> $host:/tmp/"
}

push_secrets "$@"
