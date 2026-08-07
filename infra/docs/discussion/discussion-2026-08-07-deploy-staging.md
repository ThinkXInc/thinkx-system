# infra/docs/discussion/discussion-2026-08-07-deploy-staging.md
#
# デプロイ手順の欠陥と staging 再構築まわりの議事録(2026-08-07)

イベントページを staging へ出そうとして表面化した、手順書とスクリプトの欠陥・
staging の状態についての記録。オーナー発言は原文のまま。Claude 側は要点に圧縮。

---

## 1. 手順書に commit / push が無い

**オーナー**:
> 上から順に貼れば完走します。そう言いながらいつもコミットしないと、最初のコミットが抜けているんだけど、手順書が間違っているんじゃないか。

**Claude**: そのとおりだった。`docs/デプロイ手順書.md` の通常フローは
「1 local (monorepo branch) -> PR -> develop」から始まっており、commit と push が無い。
`pr_and_merge_to_develop.sh` が見るのは `origin/$src` であって手元の HEAD ではないため、
push を忘れていると「develop は既に monorepo の内容を含んでいます。やることはありません」と
**緑で正常終了**し、`deploy_staging.sh` も成功して、古い内容が出たまま「完走」になる。

対処(コミット `4724a83`):
- 手順書に「1 local (working tree) -> local (monorepo branch) -> origin」を新設し、以降を繰り上げ。
- `pr_and_merge_to_develop.sh` に、手元 branch が origin より先行していたらコミット一覧を出して
  停止するガードを追加。未コミットがあれば「これらは出ません」と一覧表示(止めはしない。
  他トラックの WIP を巻き込まないのが D-68 の趣旨のため)。

## 2. push_assets の失敗と staging 空箱

**オーナー**(deploy_staging.sh の出力を貼付):
> thinkx: アセットが supercom-web1-stg と違うので配ります … 手元のみ ./CITYWALKPV.mp4 … これがいつも出る。
> tar: /src/thinkx/web-server/views: Cannot open: No such file or directory
> FAIL: アセットの配布に失敗しました。サーバーには触れていません
> 何かおかしいだろ　直す前に、何が起きているか説明して、原因と対処法を教えてくれ。

**Claude**(読み取りのみで実測): supercom-web1-stg / supercom-lb1-stg とも `/src` が存在せず、
`kaz` ユーザーも無く、nginx inactive、node 未導入、uptime 約20時間。**箱はあるが中身が未構築**。
prod (supercom-web1) には `/src/thinkx-system` がある。

- 「いつも出る」の正体: `push_assets.sh` は箱側の一覧取得を `2>/dev/null` で握りつぶすため、
  「宛先が存在しない」を「中身が違う」として表示し、毎回 343MB を送っていた。
  2026-07-24 の「箱が空 = ssh 不達の誤表示」と同型の再発。
- 転送先の存在確認より先に scp するため、343MB 送ったあとに tar で落ちる順序になっていた。

**オーナー**:
> わかった、思い出した。昨日、なぜか全部サーバーがリセットされたので、ステージングが今ないんだった。ステージングを立てる手順をください。

**Claude**: 構築手順(`docs/構築手順.md`)を確認。箱と ssh alias と DNS は生きているので
terraform と DNS の段は不要で、secrets 配布から流せばよい、と手順を組み立てた矢先——

**オーナー**:
> というか、別のセッションで今ステージングを立てているように見える。

**Claude**: 実機を確認したところ LB では `sudo apt install -y curl` が実行中、web では kaz 作成済み。
別セッションが構築中だった。並行して流すと apt ロックが衝突する(findings に記録済みの
`setup_webserver.sh` 2回連続 FAIL の原因)。こちらは触らないと決めて待機。

## 3. 手順書が実在しないパスを指していた

**Claude**: 構築手順 7章ほか3本が `infra/etc/push_assets.sh` を指していたが、このスクリプトは
`infra/scripts/` へ移動済み(GUIDELINES「etc/ と scripts/ の線引き」2026-07-21)。貼れば
`No such file or directory` で止まる。

**オーナー**:
> 直しておいてくれ。

**Claude**: `構築手順.md` / `運用.md` / `DNS切替手順.md` の3本を修正(コミット `9343045`)。
DECISIONS・GUIDELINES・引き継ぎ・discussion の記述は当時の記録なので変更しない。
再発防止として、手順書に出てくる `*.sh` / `*.py` のパスが実在するか機械照合するワンライナーを
findings に残した(現在 MISSING なし)。

## 4. プレースホルダ禁止

**オーナー**:
> `git add <出すファイル>` / `git commit -m "<何を変えたか>"` これそのまんま出してくれない。
> そのまま出してくるなよ

**Claude**: 手順書からも `<...>` を全廃(コミット `0905aae`)。commit は編集ディレクトリ単位
(`git add thinkx/` / `git add infra/`)に固定。`acceptance-sweep.sh <LB_IP>` は
`"$(bash infra/scripts/terraform_output.sh prod lb_public_ip)"` に置換。値の選択が要る
rollback の日付だけ `BACK_TO=release/2026-08-06` の1行ブロックに隔離した。

## 5. staging の状態(再構築後に残っていたもの)

**Claude**(実測):
- web / LB とも checkout が `monorepo` ブランチのまま。`sync_from_origin.sh staging` は
  `develop` を期待するので、そのままでは WRONG-BRANCH で止まる。
- `deploy-timer@staging.timer` が未導入。develop が進んでも自動追従しない。
- Claude Code が未導入(`claude` コマンドが無く、`claude-session.service` の unit も無い)。
  スマホの Remote Control から staging に指示する経路(D-59)が失われている。
  復旧は `setup_claude_code.sh` を流し、tmux 内で `claude --remote-control` を一度起動して
  対話ログイン(新インスタンスのため `/home/kaz/.claude` の認証は引き継がれていない)。

**オーナー**:
> attach staging したあとどうするんだっけ　スマホでstagingに指示するのは

**Claude**: 本来は起動時に systemd が tmux + `claude --remote-control` を立てるので、スマホの
アプリからセッションを選ぶだけ。attach は Mac から様子を見るときだけ。ただし現状は上記のとおり
未導入なので、先に `setup_claude_code.sh` と対話ログインが要る。

## 6. 本番へ

**オーナー**:
> 本番に 手順を

**Claude**: `bash infra/scripts/deploy_production_from_staging.sh` の1本。実行そのものが承認で、
その瞬間の `origin/develop` が `release/YYYY-MM-DD` として凍結され、production への PR・merge・
本番2台への反映まで進む。`continue? (yes/no)` で一度止まる。
なお staging は Basic 認証のため Claude 側からは中身を確認できていない(全 URL 401)。
staging の目視確認はオーナーが行う前提であることを明示して渡した。
