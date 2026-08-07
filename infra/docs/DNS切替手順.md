# thinkx-system/infra/docs/DNS切替手順.md
#
# 本番 DNS を オンプレ(123.226.234.127) → AWS LB(52.197.179.70) へ切り替える。
# 対象は apex の A レコード 3件のみ(www は存在しない・MX / store / staging は触らない)。
# TTL は 300 秒(実測 2026-07-18)。切替も戻しも最大5分で浸透する。
#

## prerequisites

```
cd ~/Sources/thinkx-system
WEB=supercom-web1
LB=supercom-lb1
LB_IP=$(bash infra/scripts/terraform_output.sh prod lb_public_ip)
```

## 1. 切替前チェック(5分)

```
bash infra/scripts/push_assets.sh $WEB thinkx
bash infra/scripts/check_request_path.sh $LB_IP $WEB $LB
bash infra/scripts/acceptance-sweep.sh $LB_IP
for d in thinkxinc.com transformism.art kazukiotsuka.com; do printf '%-20s ' $d; echo | openssl s_client -connect $LB_IP:443 -servername $d 2>/dev/null | openssl x509 -noout -enddate; done
```

## 2. Route53 で A レコードを変更(5分)

https://us-east-1.console.aws.amazon.com/route53/v2/hostedzones を開く。

3つのホストゾーンで同じ変更を1件ずつ行う:

1. thinkxinc.com のゾーン → レコード `thinkxinc.com`(A)→ 編集 → 値を `52.197.179.70` に変更 → 保存
2. kazukiotsuka.com のゾーン → レコード `kazukiotsuka.com`(A)→ 編集 → 値を `52.197.179.70` に変更 → 保存
3. transformism.art のゾーン → レコード `transformism.art`(A)→ 編集 → 値を `52.197.179.70` に変更 → 保存

apex の A 以外(MX・NS・SOA・store・staging・TXT)は変更しない。

## 3. 浸透確認(5〜10分)

```
for d in thinkxinc.com kazukiotsuka.com transformism.art; do dig +short A $d | sed "s/^/$d -> /"; done
```

3件とも `-> 52.197.179.70` になったら:

```
for d in thinkxinc.com kazukiotsuka.com transformism.art; do printf '%-20s ' $d; curl -s -o /dev/null --max-time 15 -w '%{http_code}\n' https://$d/; done
bash infra/scripts/acceptance-sweep.sh $LB_IP
```

3件とも 200・sweep 全 green なら切替完了。

## 4. 実トラフィック確認(5分)

```
ssh $LB 'sudo tail -20 /src/loadbalancer/logs/access.log'
```

実訪問者のアクセスが流れていることを目視。問い合わせフォームを1件送信し、メールが届くことを確認(SES 実測)。

## 5. 戻し方(5分)

手順2と同じ画面で 3件の A レコードの値を `123.226.234.127` に戻す → 手順3の dig で確認。
オンプレは停止していないので、DNS を戻すだけで旧環境に復帰する。

## 6. 旧環境の凍結(切替後 数日安定してから・オーナー判断)

オンプレの web / LB は当面停止しない(ロールバック先として温存。停止・撤去はオーナー判断で別途)。

GitHub の旧リポジトリ(真実が monorepo に移ったもの)をアーカイブ(読み取り専用化)する:

```
gh repo archive ThinkXInc/thinkx -y
gh repo archive ThinkXInc/kazukiotsukacom -y
gh repo archive ThinkXInc/transformism -y
gh repo archive ThinkXInc/nginx-web-root -y
gh repo archive ThinkXInc/loadbalancer -y
```

戻し方:

```
gh repo unarchive ThinkXInc/thinkx -y
```

## 凍結の対象外

- libcommon(M-4 の discord webhook 対応が残っている)
- simplicity / auth / quantz-web(独立トラックで現役)
- infra 旧リポジトリ(staging の tfstate が残っている。I-STEP3 の staging 再構築後に凍結)
