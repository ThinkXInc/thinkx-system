#!/usr/bin/env bash
# thinkx-system/infra/etc/push_rw_key.sh   【分類: 変更系(staging web の push 経路を書き込み鍵に切替)】
#
# 書き込み deploy key(deploy_thinkx-system-rw)を staging web にだけ配置する(D-55/D-56)。
# prod には配らない(push_secrets.sh も *-rw* を除外済み)。
# 前提: gen_deploy_key.sh thinkx-system-rw 済み + GitHub に Allow write access で登録済み
#
#   使い方: bash infra/etc/push_rw_key.sh

set -euo pipefail

G=$'\033[32m' R=$'\033[31m' Z=$'\033[0m'
HOST=supercom-web1-stg
KEY=infra/deploykeys/deploy_thinkx-system-rw

[ -f "$KEY" ] || { printf '%b\n' "${R}FAIL: push_rw_key $KEY が無い(先に gen_deploy_key.sh thinkx-system-rw)${Z}"; exit 1; }

scp "$KEY" "$KEY.pub" "$HOST:/tmp/"

ssh "$HOST" 'bash -s' <<'REMOTE'
sudo mv /tmp/deploy_thinkx-system-rw /tmp/deploy_thinkx-system-rw.pub /home/kaz/.ssh/
sudo chown kaz:kaz /home/kaz/.ssh/deploy_thinkx-system-rw /home/kaz/.ssh/deploy_thinkx-system-rw.pub
sudo chmod 600 /home/kaz/.ssh/deploy_thinkx-system-rw
sudo -u kaz mkdir -p /home/kaz/.ssh/config.d
sudo -u kaz tee /home/kaz/.ssh/config.d/github-thinkx-system-rw > /dev/null <<'EOF'
Host github-thinkx-system-rw
  HostName github.com
  User git
  IdentityFile /home/kaz/.ssh/deploy_thinkx-system-rw
  IdentitiesOnly yes
EOF
sudo -u kaz git -C /src/thinkx-system remote set-url --push origin git@github-thinkx-system-rw:ThinkXInc/thinkx-system.git
REMOTE

# verify  (fetch は読み取り鍵のまま・push だけ書き込み鍵で通ること)
ssh "$HOST" 'sudo -u kaz git -C /src/thinkx-system push --dry-run origin monorepo' \
  && printf '%b\n' "${G}OK: push_rw_key $HOST から thinkx-system へ push 可能(経路は push のみ切替)${Z}" \
  || printf '%b\n' "${R}FAIL: push_rw_key push --dry-run が失敗。GitHub 側の Allow write access を確認${Z}"
