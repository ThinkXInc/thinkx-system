# thinkx-system/k00bot2/deploy/deploy_ec2.md
#
# Run k00bot2 from its own branch clone and persist live data in kazukiotsuka/k00bot2.

## 最終配置

```text
/src/thinkx-system-k00bot2/k00bot2  実行コード・最新data・.env
/src/k00bot2                data永続化用の原本clone
```

`ThinkXInc/thinkx-system` のdeploy keyはread-onlyのままにする。書き込み可能な
`deploy_thinkx-system-rw` は `kazukiotsuka/k00bot2` だけに登録し、隣接cloneの
data commit/pushにのみ使う。

## 新規構築

supercom2または退避元から初回dataと `.env` を `/tmp` へ配布した後に実行する。

```zsh
cd ~/Sources/thinkx-system
ssh supercom-web1 'bash -s' < k00bot2/deploy/setup_k00bot2_ec2.sh
```

## cron

web EC2はUTC。dailyは21:10 UTC、すなわちJST 06:10に実行する。

```zsh
cd ~/Sources/thinkx-system
ssh supercom-web1 'sudo tee /etc/cron.d/k00bot2 >/dev/null; sudo chmod 644 /etc/cron.d/k00bot2' < k00bot2/deploy/k00bot2.cron
```

## data永続化

daily/monthly終了後に `run/sync_data.sh` が以下を行う。

1. `/src/thinkx-system-k00bot2/k00bot2/data` を `/src/k00bot2/data` へミラーする。
2. X生アーカイブとdaily/monthlyログを除外する。
3. `/src/k00bot2` だけでdataをcommitする。
4. `kazukiotsuka/k00bot2` へpushする。

EC2を再構築するときは `/src/k00bot2/data` からmonorepo側へdataを復元する。

## 確認

```zsh
ssh supercom-web1 'tail -20 /src/thinkx-system-k00bot2/k00bot2/data/log_daily.txt'
```
