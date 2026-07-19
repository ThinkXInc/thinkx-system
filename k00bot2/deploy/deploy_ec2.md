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

k00bot2 の行が deploy/k00bot2.cron と同じ時刻ならOK(違えば k00bot2.cron を実測に合わせてから手順5へ)

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

## 運用: コード更新の反映

```
cd ~/Sources/thinkx-system-k00bot2
ssh $WEB 'sudo -u kaz git -C /src/thinkx-system-k00bot2 pull'
```
