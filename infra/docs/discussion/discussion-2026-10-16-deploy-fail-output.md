2026-10-16 デプロイ失敗の誤判定と、スクリプト出力の読みやすさ改善（生ログ）

引用（太字）がオーナーの発言で、原文のまま。続く地の文が Claude の応答（実際に返した内容。
冗長な部分のみ圧縮）。時系列。発端は KOBITO LP の本番デプロイ（thinkx 側の記録は
thinkx/docs/discussion/discussion-2026-10-16-kobito-lp-pricing-copy.md）。確定事項は
DECISIONS.md（D-84）と findings.md 2026-10-16 が正。

> **何かおかしい　これらの動画など使われている　判定をミスしていると思われる**

（deploy の「アセットが supercom-web1 と違うので配ります」+全動画「手元のみ」の出力に対して）

ご指摘のとおり判定ミス。原因は二段で、①ルーターの動的 IP が変わり（現在 114.145.188.31、
SG の許可は旧 114.145.178.100 等 5 件）、SSH(22) が staging/prod とも締め出された。
②push_assets.sh の `rem="$(ssh ... 2>/dev/null | __norm_manifest)"` が ssh 失敗時に
rem=空文字となり「箱が空=全ファイル手元のみ」と区別できず、誤判定して配布に進み scp で
落ちる。サーバー上の動画は無傷（一覧取得も scp も失敗しており何も書いていない）。
復旧は add_current_office_ip.sh（tfvars+terraform apply を含むためオーナー実行）。
push_assets の修正（ssh 不達なら判定せず FAIL で止める）を提案し承認待ちとした。
findings に記録（f0c17e2）。

---

> **すでにある**
> **と言ってるのに変更するのはどういうこと？**
> **何が変更されるのかよくわからない　改良が必要**

（add_current_office_ip.sh が「114.145.188.31/32 は既に許可リストにある」と言いつつ
terraform の変更 plan を出したことに対して）

「既にある」は tfvars（手元の設定ファイル）の話で、実際の AWS の SG にはまだ入っていない
（前回の実行が terraform プロンプトで完走しなかった状態）。手元の設定と AWS の実態を
区別せず表示していたのが紛らわしさの正体。改良として、①「tfvars には既にある（SG に
反映済みとは限らない）」と区別して表示、②terraform の前に SG ごとの追加/削除 IP を
日本語で明示、③差分ゼロなら apply を飛ばす、④staging も「追加した/既に許可済み」を
実態どおり表示、に書き換えた（0eda4a2）。

---

> **違うので配ります**
> **が直っていないようだが**

push_assets の修正は承認待ちで未適用だった（この指摘を承認と受け取り適用）。箱の一覧取得の
exit status を見て、255=ssh 不達・非0=箱なしは判定せず FAIL で止める形に修正し、実際の
不達状態で「FAIL: ssh 不達。箱の中身は不明（配らない）」で止まることを実測確認（852ecc6）。
なお再実行で同じ表示が出たのは SSH がまだ不達のため（IP 許可の apply が未完走）。

---

> **これも読みにくすぎる**
> **改行とか（）が無駄につかわれすぎで構造化が微妙とか　だと思う**

（FAIL 4 行が同じ話を繰り返すデプロイ失敗出力に対して）

構造から修正（c62709b）。①ssh 不達は site に依らないのでホストにつき 1 回だけ判定し、
FAIL 1 行+直し方 1 行で止める。②deploy_production_from_develop.sh / deploy_staging.sh の
停止時は「ここで停止。サーバーはまだ何も変わっていない」→「済み:」「次に:」の定型に統一。
修正後の出力:

```
FAIL: supercom-web1 へ ssh 不達。アセットは確認も配布もできない
  典型は IP 許可切れ。直すには: bash infra/scripts/add_current_office_ip.sh

ここで停止。サーバーはまだ何も変わっていない
  済み: release の凍結・production への取り込み
  次に: 上の FAIL の原因を直して、同じコマンドをもう一度
```

---

> **これだとどの部分が変更されているのかわからないのだが　改善できないの？**

（terraform の生の plan が SG の ingress をセット丸ごと -旧/+新 で表示することに対して）

terraform の表示仕様で直せないため、方式を変えた（0d069fd・D-84）。plan を -out で保存し、
show -json から人間語に要約して見せ、yes ならその保存した plan をそのまま適用する
（要約と適用内容の一致を plan ファイルが保証。承認は terraform のプロンプトでなく
スクリプト自前の yes/no）。実際の差分でテストした出力:

```
==== これから適用される変更 prod ====
supercom-prod-lb-sg:
  ポート22: 許可IPに追加 114.145.188.31/32
supercom-prod-web-sg:
  ポート22: 許可IPに追加 114.145.188.31/32
  ポート8000-8009 → ポート8000-8099 に変更: backend ports from LB SG only
この変更を適用するか (yes/no):
```

読めない plan に埋まっていた中身はこの 3 行だけだった。3 行目の 8000-8099 への拡大は
IP とは別の変更だが、オーナー自身の指示（2026-09-17「サイト追加のたびに広げない」・
2225d90）でコードだけ変わり実機に未適用だった分で、一緒に適用されて問題ない。
作成/削除が plan に混ざった場合は「no で止めて調べること」と注意が出る。

---

## セッション終了時点の状態

- 済み: push_assets の誤判定修正・deploy 2 本の停止時出力の定型化・
  add_current_office_ip の差分要約方式（いずれも monorepo に push 済み。852ecc6 / c62709b / 0eda4a2 / 0d069fd）
- 未完（オーナー実行待ち）: ①`bash infra/scripts/add_current_office_ip.sh`（terraform の
  yes 込み）→ 4 台 SSH ok の確認、②`bash infra/scripts/deploy_production_from_develop.sh`
  のやり直し（release 凍結と production 取り込みは済み。残りはサーバー反映のみ）、
  ③staging への動画アセット配布も SSH 復旧後に自動で揃う
