# health check(死活監視 → Discord 通知)

仕組み: prod LB の systemd timer が 1 分ごとに各サイトへ curl し、落ちたら専用 Discord
チャンネルに通知する(up→down 1 回・復旧 1 回・落ち続けは 1 時間ごと)。LB 自身の死角は
Mac の launchd が 5 分ごとに LB(thinkxinc.com)と staging(EC2 が running のときだけ)を見る。
本体は `infra/scripts/health_check.sh` 1 本(LB と Mac で env だけ違う)。
設定(監視対象など)はリポジトリ内 `infra/health_check/loadbalancer.yaml` / `local.yaml` が正
(変更は普通のコミット+デプロイで流れる。設定は YAML — .env は秘密情報を意味するので使わない)。
**git に入れないのは webhook URL の 1 行だけ**で、新しい秘密ファイルは作らず既存の .env に
相乗りする(キー名 `HEALTH_DISCORD_WEBHOOK_URL`。LB は `/src/loadbalancer/.env`
(LB の .env はこれが最初)、Mac は `thinkx/web-server/.env`)。

前提1: Discord に専用チャンネルを作る(他と混ぜない・mute しない)。
チャンネル設定 → 連携サービス → ウェブフック → 新しいウェブフック → URL をコピー。

前提2: LB の /src/thinkx-system に health_check.sh が入っていること
(この機能を入れた release を `deploy_production_from_develop.sh` で本番に出してから行う)。

変数(以降の全ブロック共通。Mac のローカル端末で最初に 1 回設定する。URL は自分のものに置き換える):

```
WEBHOOK='https://discord.com/api/webhooks/xxxx/yyyy'
```

通知テスト(専用チャンネルに test と出れば webhook は正しい):

```
curl -sS -m 10 -H 'Content-Type: application/json' -d '{"content":"test"}' "$WEBHOOK"
```

## LB に入れる(Mac のローカル端末から)

webhook を書く(LB の .env に 1 行追記。監視対象はリポジトリの infra/health_check/loadbalancer.yaml が正):

```
ssh supercom-lb1 "sudo touch /src/loadbalancer/.env && sudo chmod 600 /src/loadbalancer/.env && sudo tee -a /src/loadbalancer/.env >/dev/null" <<EOF
HEALTH_DISCORD_WEBHOOK_URL="$WEBHOOK"
EOF
```

timer を入れる:

```
cd ~/Sources/thinkx-system
ssh supercom-lb1 'sudo bash -s' < infra/setup/setup_health_check.sh
```

1 回手で流して動きを見る(全サイト正常なら何も通知されず、静かに終わる):

```
ssh supercom-lb1 'sudo HEALTH_CONFIG=/src/thinkx-system/infra/health_check/loadbalancer.yaml bash /src/thinkx-system/infra/scripts/health_check.sh'
```

## Mac に入れる(Mac のローカル端末で)

webhook を書く(既存の thinkx/web-server/.env に 1 行追記。監視対象はリポジトリの infra/health_check/local.yaml が正):

```
printf 'HEALTH_DISCORD_WEBHOOK_URL="%s"\n' "$WEBHOOK" >> ~/Sources/thinkx-system/thinkx/web-server/.env
```

launchd に載せる(5 分ごと):

```
cd ~/Sources/thinkx-system
cp infra/health_check/com.thinkx.health-check.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.thinkx.health-check.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.thinkx.health-check.plist
```

## 状態を見る

LB 側:

```
ssh supercom-lb1 'systemctl list-timers health-check.timer --no-pager && sudo journalctl -u health-check -n 20 --no-pager'
```

Mac 側:

```
launchctl list | grep com.thinkx.health-check
tail -20 /tmp/com.thinkx.health-check.log
```

## 止める

LB 側:

```
ssh supercom-lb1 'sudo systemctl disable --now health-check.timer'
```

Mac 側:

```
launchctl unload ~/Library/LaunchAgents/com.thinkx.health-check.plist
```
