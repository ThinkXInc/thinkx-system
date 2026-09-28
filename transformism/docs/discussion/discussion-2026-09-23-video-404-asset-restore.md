# 2026-09-23 transformism 本番 /video/ 404 調査と復旧の記録（生ログ）

引用（太字）がオーナーの発言で、原文のまま。続く地の文が Claude の応答（実際に返した内容。
冗長な部分のみ圧縮）。時系列。セッションは 2026-09-23 に開始し、オーナーによる復旧実行と
本番確認を経て 2026-09-28 に終了した。事実関係の正本は `transformism/findings.md`
「2026-09-23: 本番 /video/BWVFHDPromo1.14_compress.mp4 が 404」の項。

> **transformismのサイトの /video/BWVFHDPromo1.14_compress.mp4 が404になっている　確認してくれ　アセットが飛んでいないかもしれない**

調査の結論: **アセットは飛んでいない**が、monorepo 移行時に配布経路から漏れていた。

- 実測: `https://transformism.art/video/BWVFHDPromo1.14_compress.mp4` → 404
  （`www.transformism.com` 経由も 404）。サイト本体 `/` は 200。参照元は
  `transformism/web-server/views/templates/index.html:135`（トップの背景動画）。
- 原因は3点の連鎖:
  1. 旧リポジトリ `.gitignore:34` の `web-server/views/video/*` により動画はもともと git 管理外。
  2. monorepo 取り込み（M-2）は git ref のツリーコピーだったため、git 管理外の
     `views/video/` ごと monorepo に存在しない。
  3. `infra/scripts/push_assets.sh` は「transformism / kazukiotsukacom は動画を持たない。
     これは正常な状態」という注記つきで views/video 不在サイトを黙ってスキップする。
     この前提が実態と食い違っていた（transformism は動画を1本持つ）。
- 実体は凍結中の旧リポジトリに無事:
  `~/Sources/transformism/web-server/views/video/BWVFHDPromo1.14_compress.mp4`
  （11,613,690 bytes / sha256 `4cdafd3787…d4f1296e`）。
- 直し方: 旧リポジトリから monorepo へこの mp4 をコピーするだけで経路が繋がる
  （thinkx と同じ「git 管理外 + push_assets 配布」方式。monorepo 側 .gitignore にも
  同じ除外があり git には入らない）。deploy スクリプトは既に transformism を
  push_assets.sh に渡しているため、スクリプト変更は不要。
- Claude によるコピー実行は承認されなかったため、コピー → staging 配布 → 本番配布 →
  実測確認の貼り付け用コマンド4ブロックをオーナーへ提示した。
- findings.md に記録済み。付随修正候補として push_assets.sh の
  「transformism は動画を持たない」注記の文言修正を挙げた（人間判断）。

---

> **bash infra/scripts/push_assets.sh supercom-web1-stg transformism**
> **transformism: アセットが supercom-web1-stg と違うので配ります**
> **1c1**
> **  箱のみ**
> **  手元のみ ./BWVFHDPromo1.14_compress.mp4 11613690**
> **ssh: connect to host 57.182.107.57 port 22: Operation timed out**
> **scp: Connection closed**
> **FAIL: transformism の assets 転送または展開に失敗**
> **FAIL: push_assets -> supercom-web1-stg 失敗 1 件(配布 0 件・一致 0 件)**

staging の箱（57.182.107.57:22）への SSH がタイムアウト。切り分けを開始:
`staging.thinkxinc.com` → 000（接続不可）、`thinkxinc.com` → 200。staging 側の
到達性の問題（箱が停止中）と判断。

---

> **ステージング起動してる**

起動後の再実測で staging の復帰を確認:

- `staging.thinkxinc.com` → 401（Basic 認証 = LB 正常応答。DNS は LB EIP 52.68.142.190
  で D-53 の EIP 台帳どおり）
- `staging.transformism.art/video/…` → 401（Basic 認証の手前まで到達 = 箱に届いている）

---

> **OK できた　本番で確認済み**

オーナーが復旧を実行・本番確認済み。Claude 側でも実測で裏取り:
`https://transformism.art/video/BWVFHDPromo1.14_compress.mp4` が HEAD 200 / Range 206
（正常配信）。findings.md に **[解決済 2026-09-28]** を追記した。

---

> **このセッションは終了する　所定の方法で記録してくれ**

記録一式を作成（本議事録・findings 解決追記）。新規の決定事項・オーナー指示は
このセッションでは発生していないため、DECISIONS.md / GUIDELINES.md への追記は無し。
未対応で残るのは push_assets.sh の注記文言修正（人間判断待ち・findings 記載）。

## 到達点

本番 transformism の背景動画 404 は、monorepo 移行で git 管理外アセットが運ばれず、
配布スクリプトも「transformism に動画は無い」前提でスキップしていたことが原因だった。
旧リポジトリから monorepo へ mp4 を戻し push_assets.sh で配布して復旧、本番で
HEAD 200 / Range 206 を実測確認した。今後同種の 404 が出たら「git 管理外アセットが
移行・配布経路に乗っているか」を最初に疑う。
