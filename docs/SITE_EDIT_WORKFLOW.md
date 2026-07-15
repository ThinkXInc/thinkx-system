# サイト編集ワークフロー規範(E トラック) v0.9-draft

対象: monorepo 化・EC2 カットオーバー後の、静的サイト群(thinkx / kazukiotsukacom /
transformism)の日常編集。正本はこの1箇所(monorepo の docs/SITE_EDIT_WORKFLOW.md)。
前提: M トラック完了(monorepo が staging EC2 で稼働)+ カットオーバー完了
(monorepo master = 本番)。**カットオーバー前は本文書は発効しない。**

確定タイミングで埋める項: <STAGING_EC2> <PROD_EC2> の実ホスト名、
staging の Basic 認証情報の受け渡し方法。

## 全体の型

```
[スマホ/ブラウザ] ──Remote Control── [staging EC2 の Claude Code 常駐]
  1. master 起点でセッションブランチ site/YYYY-MM-DD-<内容> を作成
  2. 編集(コード変更とゴールデン更新は同一ブランチ)
  3. ビルド → staging サービス再起動 → staging URL を提示
  4. 人間: スマホで見た目確認・会話で diff 確認
  5. OK → push → gh pr create → PR リンク提示
  6. 人間: GitHub(モバイル可)で Rebase and merge ← 本番反映の承認ゲート
  7. Claude Code: 本番へ SSM → git pull → ビルド → restart → sweep → 報告
```

## セッション規律

- 1 編集セッション = 1 ブランチ = 1 PR。ブランチは使い捨て
  (マージ後は削除。rebase マージで SHA が変わるため、続行・再利用は禁止)
- ブランチは常に**最新の origin/master** から切る(切る前に git fetch)
- staging への反映 = そのセッションブランチを staging ワーキングコピーに
  checkout してビルド・再起動する。**永続 staging ブランチは存在させない**
  (staging で見えるものは厳密に「master + 今回の変更」のみ)
- やめた変更はブランチごと破棄し、staging を master に戻す

## テスト規律

- ページ・ルート・URL の追加/変更/削除を行ったら、同一ブランチで
  該当サイトの web-server/tests/golden/ を更新する。PR の diff には
  コード変更とゴールデン変更が 1 対 1 で対応して並ぶこと
- **sweep が落ちたときにゴールデンを黙って再生成して通すことは禁止**。
  ゴールデン変更は常に「意図したページ変更の反映」として PR 説明に明記する
- 本番反映(手順 7)後、本番 URL に対して全サイトの sweep を実行し green を報告

## 禁止事項

- master への直接 push(全変更は PR 経由。マージは人間のみ)
- 本番サーバー上での直接編集(変更は必ずリポジトリ経由)
- vendored libcommon スナップショットの編集(修正は libcommon/ 原本 → 再 bake)
- transformism のコメントアウト済みルート群の「復活」「整理」
  (本番未投入の意図的 WIP — transformism/CLAUDE.md 参照)
- staging のアクセス制限(Basic 認証 / noindex)の解除

## Remote Control 常駐(staging EC2)

- サーバーモードで常駐: `claude remote-control --spawn worktree`
  (接続ごとに独自 git worktree — 複数セッション・複数人の編集が相互隔離される)
- tmux 内で起動し、systemd で tmux ごと自動起動(EC2 再起動対応)。
  具体 unit は runbooks/remote-control.md(infra 側)に置く
- ネットワーク断が約 10 分続くとプロセス終了・URL 失効 → systemd が再起動し
  新 URL が発行される。新 URL の確認は SSM で tmux attach、
  またはアプリのセッション一覧(自アカウント)から

## 非開発者との共有

- 共有はセッション URL の共有のみ(SSH/SSM は開発者専用)
- URL はパスワードと同様に扱う(知っていれば接続できる)。
  プロセス再起動で失効するため恒久共有はできない — 都度渡す
- 共有セッションは worktree 隔離された編集・staging 確認まで。
  **本番反映は GitHub マージ権限(人間のアカウント)が必須**のため、
  URL 共有相手は本番に触れない(構造的ゲート)
- 使用量はホストの契約(自アカウント)で消費される

## 本番反映(手順 7 の詳細)

- マージ後、Claude Code が <PROD_EC2> へ SSM 接続し:
  git fetch → git checkout master → git pull → 対象サイトのビルド →
  systemctl restart uwsgi_<site> → curl でゴールデン sweep → 結果報告
- 反映は**変更のあったサイトのみ**(monorepo でも再起動単位はサイト別)
- sweep が落ちたら: 直前の master へ git で戻して再ビルド・再起動(ロールバック)し、
  原因調査は staging で行う。本番上でのデバッグは禁止
