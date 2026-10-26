# 2026-10-16 「K00BOT が止まっている」報告の切り分け(生ログ)

引用(太字)がオーナーの発言で、原文のまま。続く地の文が Claude の応答(実際に返した内容。
冗長な部分のみ圧縮)。時系列。詳細な実測記録は `infra/findings.md`(2026-10-16 の k00bot2 節)、
観測の承認ケースは `docs/approval_cases_v2.md` AP が正。

> **K00BOTが止まっているから調べて**

実測の結論は**稼働中**でした。

- web1 の cron(`/etc/cron.d/k00bot2`)は設置済み・daily 21:10 UTC(JST 06:10)で毎日起動。
- 今朝(2026-10-15T21:10Z = JST 10/16 06:10)の run は 2/2 投稿成功
  (x_post_id=2110840650329653264 / 2110840693522665527)。両方とも X 上で公開を確認
  (syndication API で本文取得。@K00TSUKA)。data repo(kazukiotsuka/k00bot2)への sync push も成功。

「止まって見えた」原因は**断続的な投稿失敗日**です。sync 日付(UTC)で 10-05・10-06・10-11・10-12、
9月も 9-12・9-13・9-15・9-20・9-23・9-26 が欠落。該当日のログは全て
`X API error 403 Forbidden: You are not permitted to perform this action.`(remaining=98〜99 →
レート制限ではない)。認証は毎回成功しており、2026-08-12 の 402(クレジット枯渇)とは別物。
翌日〜数日で自然回復を繰り返しています。X free tier の不安定さか投稿内容依存(重複判定等)かは
ログからは確定できません。

付随して見つけた点(findings に記録・勝手には直していない):

1. post_daily.py は 403 で**未捕捉例外のまま落ちる経路**があり、1件目で落ちると [fail] 行すら
   残らず sync も走らない。失敗を捕捉して残候補スキップ+sync まで完走する形が望ましい
   (k00bot2 ブランチの修正)。
2. 前回(2026-08-12)と今回で同じ切り分けを2回手書きした。生死観測 wrapper
   (`k00bot_check.py`: log tail + sync 日付一覧 + 投稿公開確認)の新設を次の一手として提案
   (approval_cases_v2.md AP)。
3. 最初の ssh は Operation timed out、数分後の再試行で成功。SG には現 IP(114.145.188.31/32)が
   登録済みだった(同日の add_current_office_ip 適用直後の揺らぎか)。

> **セッションを閉じる 記録だけいつものやりかたで**

記録一式(本議事録 + findings 追記済み + approval_cases AP 追記済み)を commit。
DECISIONS・GUIDELINES は新規事項なし(オーナーの新しい決定・指示が無かったため)。
403 の例外捕捉修正に進むかどうかは未指示のまま(次セッションの判断材料)。
