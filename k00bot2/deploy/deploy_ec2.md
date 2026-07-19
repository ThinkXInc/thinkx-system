# k00bot2/deploy/deploy_ec2.md
#
# supercom2 で動いている k00bot2(X 投稿ボット)を web(EC2)で同一に動かす。
# cron 有効化(手順5)は supercom2 の cron 停止とセットで行う(二重投稿防止)。
#

## prerequisites

```
cd ~/Sources/thinkx-system-k00bot2
SRC=supercom2
SRCPATH=/src/k00bot2
WEB=supercom-web1
```

## 1. supercom2 から .env と data を取得(1分)

```
scp $SRC:$SRCPATH/.env /tmp/k00bot2.env
ssh $SRC "tar czf /tmp/k00bot2-data.tgz -C $SRCPATH data"
scp $SRC:/tmp/k00bot2-data.tgz /tmp/k00bot2-data.tgz
```

## 2. web へ配布(1分)

```
scp /tmp/k00bot2.env /tmp/k00bot2-data.tgz $WEB:/tmp/
```

## 3. web: 構築(5分)

```
ssh $WEB 'bash -s' < k00bot2/deploy/setup_k00bot2_ec2.sh
```

末尾が緑(OK: k00bot2 dry-run 投稿候補あり)ならOK

## 4. supercom2 の cron を確認(1分)

```
ssh $SRC 'crontab -l'
```

k00bot2 の行が deploy/k00bot2.cron の JST 換算(コメント行)と同じ時刻ならOK(違えば k00bot2.cron を実測の UTC 換算に直してから手順5へ。web EC2 は UTC・supercom2 は JST)

## 5. 切替: supercom2 停止 → web 有効化(1分)

```
ssh $SRC 'crontab -l > /tmp/crontab.bak.k00bot2; crontab -l | grep -v k00bot2 | crontab -; crontab -l'
ssh $WEB 'sudo tee /etc/cron.d/k00bot2 >/dev/null; sudo chmod 644 /etc/cron.d/k00bot2; ls -l /etc/cron.d/k00bot2' < k00bot2/deploy/k00bot2.cron
```

supercom2 側の出力から k00bot2 の行が消えていて、web 側に /etc/cron.d/k00bot2 が見えればOK

## 6. 翌日の投稿確認

```
ssh $WEB 'tail -20 /src/k00bot2/data/log_daily.txt'
```

## 7. data 自動 push 用の RW deploy key(初回のみ)

data は git 管理(2026-07-19 裁定)で、daily / monthly の run スクリプトが EC2 から commit + push する。
既存の deploy_thinkx-system は read-only(D-1)のため、push 専用の鍵を EC2 上で生成して追加登録する。

```
ssh $WEB 'sudo -u kaz ssh-keygen -t ed25519 -f /home/kaz/.ssh/deploy_thinkx-system-rw -N "" -C "supercom-web:thinkx-system:rw"'
ssh $WEB 'printf "\nHost github-thinkx-system-rw\n    HostName github.com\n    User git\n    IdentityFile ~/.ssh/deploy_thinkx-system-rw\n    IdentitiesOnly yes\n" | sudo -u kaz tee -a /home/kaz/.ssh/config >/dev/null'
ssh $WEB 'sudo -u kaz cat /home/kaz/.ssh/deploy_thinkx-system-rw.pub'
```

GitHub → ThinkXInc/thinkx-system → Settings → Deploy keys → Add deploy key に貼る。
Title: supercom-web-k00bot2-rw / **Allow write access: チェックする**(D-1 read-only 原則の意図的例外。用途は k00bot2 data の自動 push のみ)

```
ssh $WEB 'sudo -u kaz ssh -T git@github-thinkx-system-rw 2>&1 | head -1'
ssh $WEB 'sudo -u kaz git -C /src/thinkx-system-k00bot2 remote set-url --push origin git@github-thinkx-system-rw:ThinkXInc/thinkx-system.git'
```

Hi ThinkXInc/thinkx-system! が出ればOK

## 8. 初回 data 取り込み(EC2 の最新実データを repo へ・初回のみ)

```
ssh $WEB 'cd /src/k00bot2 && sudo -u kaz git add data && sudo -u kaz git commit -m "data(k00bot2): initial import (supercom2 live data)" && sudo -u kaz git push'
```

## 運用: コード更新の反映

```
cd ~/Sources/thinkx-system-k00bot2
ssh $WEB 'sudo -u kaz git -C /src/thinkx-system-k00bot2 pull'
```

data は EC2 側の cron が commit + push するため、Mac 側は `git pull` で最新データを取得する(tar 移行は初回のみ)。
