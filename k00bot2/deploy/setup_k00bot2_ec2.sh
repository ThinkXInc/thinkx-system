# k00bot2(X 投稿ボット・supercom2 相当)を web(EC2)へ構築する — 変更系
#
# prerequisites:
#  - setup_user.sh / setup_webserver.sh / clone_monorepo.sh 済み(/src/thinkx-system)
#  - /tmp/k00bot2.env(supercom2 の .env。deploy_ec2.md 手順2で配布)
#  - /tmp/k00bot2-data.tgz(supercom2 の data/ 実データ。deploy_ec2.md 手順2で配布)
#  - cron はここでは入れない(二重投稿防止。deploy_ec2.md 手順5で supercom2 停止とセットで入れる)

# k00bot2 ブランチの worktree(/src/thinkx-system 本体の checkout は monorepo のまま動かさない)
cd /src/thinkx-system
sudo -u kaz git fetch origin k00bot2
[ -d /src/thinkx-system-k00bot2 ] || sudo -u kaz git worktree add --track -b k00bot2 /src/thinkx-system-k00bot2 origin/k00bot2
sudo -u kaz git -C /src/thinkx-system-k00bot2 pull
sudo ln -sfn /src/thinkx-system-k00bot2/k00bot2 /src/k00bot2

# data 自動 commit/push 用の git identity と push 先(deploy_ec2.md 手順7 で RW 鍵を作った前提)
sudo -u kaz git -C /src/thinkx-system-k00bot2 config user.name "k00bot2-bot"
sudo -u kaz git -C /src/thinkx-system-k00bot2 config user.email "kaz@thinkxinc.com"
[ -f /home/kaz/.ssh/deploy_thinkx-system-rw ] && sudo -u kaz git -C /src/thinkx-system-k00bot2 remote set-url --push origin git@github-thinkx-system-rw:ThinkXInc/thinkx-system.git || printf '\033[33mWARN: RW deploy key 未配置。data の自動 push は失敗する(deploy_ec2.md 手順7)\033[0m\n'

# .env  (git 管理外。/tmp/k00bot2.env を配った前提)
[ -f /tmp/k00bot2.env ] && sudo install -o kaz -g serveradmins -m 640 /tmp/k00bot2.env /src/k00bot2/.env || printf '\033[33mWARN: k00bot2.env 未配布(deploy_ec2.md 手順2)\033[0m\n'

# data  (git 管理外の実データ。posted_candidate_ids 等の状態を supercom2 から引き継ぐ)
[ -f /tmp/k00bot2-data.tgz ] && sudo -u kaz tar xzf /tmp/k00bot2-data.tgz -C /src/k00bot2 || printf '\033[33mWARN: k00bot2-data.tgz 未配布(deploy_ec2.md 手順2)\033[0m\n'

# venv
cd /src/k00bot2
sudo -u kaz python3 -m venv venv
sudo -u kaz ./venv/bin/pip install --upgrade pip
sudo -u kaz ./venv/bin/pip install -r requirements.txt
sudo -u kaz chmod +x run/daily.sh run/monthly.sh

# verify  (dry-run: X へは投稿しない。末尾に色で成否: 緑=投稿候補が出た / 黄=候補なし / 赤=実行失敗)
out=$(sudo -u kaz ./venv/bin/python -m scripts.pipeline.post_daily --dry-run 2>&1)
printf '%s\n' "$out"
printf '%s' "$out" | grep -q 'DRY RUN' && printf '\033[32mOK: k00bot2 dry-run 投稿候補あり\033[0m\n' || { printf '%s' "$out" | grep -q '\[skip\]' && printf '\033[33mWARN: k00bot2 dry-run 候補なし(data 移行を確認)\033[0m\n' || printf '\033[31mFAIL: k00bot2 dry-run 実行失敗\033[0m\n'; }
