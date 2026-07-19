#!/usr/bin/env bash
# thinkx-system/k00bot2/deploy/setup_k00bot2_ec2.sh
#
# Build k00bot2 in the monorepo and its adjacent data persistence clone. 変更系。

set -euo pipefail

MONOREPO=/src/thinkx-system
APP_ROOT="$MONOREPO/k00bot2"
DATA_REPO=/src/k00bot2
DATA_REMOTE=git@github-thinkx-system-rw:kazukiotsuka/k00bot2.git

sudo -u kaz git -C "$MONOREPO" pull --ff-only origin monorepo
[ -d "$APP_ROOT" ] || { echo "[error] monorepo does not contain k00bot2: $APP_ROOT"; exit 1; }
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
