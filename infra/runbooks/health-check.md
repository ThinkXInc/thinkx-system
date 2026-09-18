# health check(死活監視 → Discord 通知)

仕組み: prod LB の systemd timer が 1 分ごとに各サイトへ curl し、落ちたら専用 Discord
チャンネルに通知する(up→down 1 回・復旧 1 回・落ち続けは 1 時間ごと)。LB 自身の死角は
Mac の launchd が 5 分ごとに LB(thinkxinc.com)と staging(EC2 が running のときだけ)を見る。
本体は `infra/scripts/health_check.sh` 1 本(LB と Mac で env だけ違う)。

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

設定を書く:

```
ssh supercom-lb1 "sudo tee /etc/supercom-health.env >/dev/null && sudo chmod 600 /etc/supercom-health.env" <<EOF
DISCORD_WEBHOOK_URL="$WEBHOOK"
SITES="thinkxinc=https://thinkxinc.com/ nntm=https://nntmapp.com/ truetech=https://truetechjapan.com/ transformism=https://transformism.art/ kazukiotsuka=https://kazukiotsuka.com/"
EOF
```

timer を入れる:

```
cd ~/Sources/thinkx-system
ssh supercom-lb1 'sudo bash -s' < infra/setup/setup_health_check.sh
```

1 回手で流して動きを見る(全サイト正常なら何も通知されず、静かに終わる):

```
ssh supercom-lb1 'sudo HEALTH_ENV=/etc/supercom-health.env bash /src/thinkx-system/infra/scripts/health_check.sh'
```

## Mac に入れる(Mac のローカル端末で)

設定を書く:

```
cat > ~/.supercom-health.env <<EOF
DISCORD_WEBHOOK_URL="$WEBHOOK"
SITES="lb=https://thinkxinc.com/"
STAGING_GATED_URL="https://staging.thinkxinc.com/"
STATE_DIR="$HOME/.supercom-health-state"
EOF
chmod 600 ~/.supercom-health.env
```

launchd に載せる(5 分ごと):

```
cd ~/Sources/thinkx-system
cp infra/health/com.thinkx.health-check.plist ~/Library/LaunchAgents/
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
