#!/usr/bin/env bash
# thinkx-system/k00bot2/deploy/setup_k00bot2_ec2.sh
#
# Build k00bot2 from its own branch clone and the adjacent data persistence clone. 変更系。
# monorepo への merge は revert 済み(719e856)のため、実行コードは k00bot2 ブランチの
# 独立 clone /src/thinkx-system-k00bot2 に置く。/src/thinkx-system(production 追従)には置かない。

set -euo pipefail

APP_CLONE=/src/thinkx-system-k00bot2
APP_ROOT="$APP_CLONE/k00bot2"
APP_REMOTE=git@github-thinkx-system:ThinkXInc/thinkx-system.git
DATA_REPO=/src/k00bot2
DATA_REMOTE=git@github-thinkx-system-rw:kazukiotsuka/k00bot2.git

if [ ! -d "$APP_CLONE/.git" ]; then
  sudo -u kaz git clone --branch k00bot2 "$APP_REMOTE" "$APP_CLONE"
fi
sudo -u kaz git -C "$APP_CLONE" pull --ff-only origin k00bot2
[ -d "$APP_ROOT" ] || { echo "[error] k00bot2 branch does not contain k00bot2/: $APP_ROOT"; exit 1; }
[ ! -L "$DATA_REPO" ] || { echo "[error] legacy symlink remains: $DATA_REPO"; exit 1; }

if [ ! -d "$DATA_REPO/.git" ]; then
  sudo -u kaz git clone "$DATA_REMOTE" "$DATA_REPO"
fi

sudo -u kaz git -C "$DATA_REPO" config user.name "k00bot2-bot"
sudo -u kaz git -C "$DATA_REPO" config user.email "kaz@thinkxinc.com"

if [ -d "$DATA_REPO/data" ]; then
  sudo -u kaz tar cf - -C "$DATA_REPO" data | sudo -u kaz tar xf - -C "$APP_ROOT"
fi
if [ -f /tmp/k00bot2-data.tgz ]; then
  sudo -u kaz tar xzf /tmp/k00bot2-data.tgz -C "$APP_ROOT"
fi
if [ -f /tmp/k00bot2.env ]; then
  sudo install -o kaz -g serveradmins -m 640 /tmp/k00bot2.env "$APP_ROOT/.env"
fi

cd "$APP_ROOT"
if [ ! -x venv/bin/python ]; then
  sudo -u kaz python3 -m venv venv
fi
sudo -u kaz ./venv/bin/pip install --upgrade pip
sudo -u kaz ./venv/bin/pip install -r requirements.txt
sudo -u kaz chmod +x run/daily.sh run/monthly.sh run/sync_data.sh

out=$(sudo -u kaz ./venv/bin/python -m scripts.pipeline.post_daily --dry-run 2>&1)
printf '%s\n' "$out"
printf '%s' "$out" | grep -q 'DRY RUN' && printf '\033[32mOK: k00bot2 dry-run 投稿候補あり\033[0m\n' || { printf '%s' "$out" | grep -q '\[skip\]' && printf '\033[33mWARN: k00bot2 dry-run 候補なし(data を確認)\033[0m\n' || printf '\033[31mFAIL: k00bot2 dry-run 実行失敗\033[0m\n'; }
