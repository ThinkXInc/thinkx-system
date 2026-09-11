# thinkx-system/docs/approval_cases_v1.md

# 承認ケース集(コーパス) v1

実際に承認プロンプトが出た(または出るべき/出るべきでない)コマンドを生のまま貯める場所。
**これは材料であって規範ではない。** 距離を置く 3 つの文書の関係:

- **enforce の正**: `.claude/settings.json`(deny / ask / allow)。実際に止めているのはこれ。ここを複製しない。
- **判定基準(蒸留)**: `docs/DEPLOY_APPROVAL_LEVELS.md`「承認削減の判定基準」。観測系→スクリプト / 文書系→git レビュー / 変更系→残す。
- **本ファイル(コーパス)**: 生の事例。パターンが溜まったら判定基準へ蒸留する。infra の findings→DECISIONS と同じ位置。

## バージョンとライフサイクル(重要)

- **v1(本ファイル)= 閉じたバッチ。** ここに集めた事例を材料に、承認削減のコマンド/スクリプト/フックを一式作る。
  作り終えたら v1 はクローズし、`docs/archive/approval_cases/v1.md` へ移す(archive は非規範・CLAUDE.md 文書優先順位 5)。
- **運用開始後の新規ケースは v2 に貯める。** `docs/approval_cases_v2.md` を新規に開き、同じ書式で足していく。
  v1 は「初期構築の材料」、v2 以降は「運用中に出た差分」。混ぜない。
- したがって v1 に新しいケースを足すのは「構築物をまだ作り終えていない間」だけ。作り終えたら v1 は凍結して archive、以後は v2。

## 追記のしかた

新しく承認が出たコマンドに当たったら、下に 1 ケース足す。フィールドは 5 つ:

- **生コマンド(要点)**: 実際に打ったもの(長ければ要点)。
- **承認の引き金**: なぜ止まったか(どの ask/deny 語にマッチしたか)。
- **クラス**: 観測 / 編集 / 資産 / 変更 / 一度きり。
- **正しい形**: 畳んだ形 or 使うべき専用ツール。
- **残るゲート**: 無承認化しても残す承認(公開・見た目 OK など)。無ければ「なし」。

## 判定の 3 問(蒸留の軸)

1. **作業に合う道具は何か。** 編集=Edit、画像=magick、繰り返す観測=固定スクリプト、ツールの形の承認=フック、本当に一度きり=生の Bash。
2. **相手は安全か。** localhost の GET・読み取り観測=安全。外部・本番・副作用のある操作=安全でない。
3. **レビュー成果物は何か。** テキスト=diff(Edit)、見た目・バイナリ=レンダリング結果/スクショ、観測=OK/MISMATCH の突き合わせ。

「Bash かどうか」「長いか」は軸ではない。

---

## 事例(2026-09-05〜06 セッション由来)

### A. staging の state 遷移ウォッチ
- **生**: `ssh supercom-web1-stg 'prev=""; for i in $(seq 1 54); do curl -s .../connect/state | python3 -c "..."; ...; sleep 5; done; journalctl -u claude_connect'`
- **引き金**: `ssh`(ask)。中の curl も同様。
- **クラス**: 観測。
- **正しい形**: `python3 infra/scripts/stg.py watch`(ssh を subprocess に畳むと ask にマッチしない。実測で無承認)。
- **残るゲート**: なし。

### B. staging の環境発見(一度きり)
- **生**: `ssh supercom-web1-stg 'id -un; hostname; timedatectl ...; ss -ltn | grep 8008; curl web1:8008/connect/state; getent hosts web1; systemctl is-active ...; tmux ls; journalctl'`
- **引き金**: `ssh`(ask)。
- **クラス**: 観測(TZ・bind・DNS の発見は 1 回で意味が尽きる)。
- **正しい形**: 発見部分は承認 1 回で流し、結果は定数化して findings に記録。繰り返す検証部分(unit・tmux・8008・別名解決)だけ `stg.py doctor` に昇格。
- **残るゲート**: なし。

### C. 段落間の改行足し(整形)
- **生**: `python3 - <<'EOF' ... s.replace("…。\nWEIRD","…。\n\nWEIRD") ... EOF; python3 build_ueda2.py && curl -s http://127.0.0.1:5000/... | grep`
- **引き金**: `curl`(ask)。Python の heredoc も build も単体では止まらない。
- **クラス**: 編集 + 観測。
- **正しい形**: 書き換えは Edit ツール(diff で見える。heredoc の `s.replace` は Edit の再発明で不可視)。確認はビルドスクリプトに urllib で畳み、可視コマンドを `python3` に一本化。
- **残るゲート**: 公開(staging/本番)。

### D. 記事見出しの書き換え(内容変更・C と同型だが性質が違う)
- **生**: C と同じ形。中身が `{"head": "ASDと女性と自然選択"}` → `{"head": "文明の進歩とともに思考は分類的になったのか"}`。
- **引き金**: `curl`(ask)。ただし本当のゲートはここではない。
- **クラス**: 編集(内容)。thinkx 実記事の見出し=原稿の変更。
- **正しい形**: Edit(diff=原文→提案)。**依頼済みの変更ならそのまま実行**、依頼の範囲を超えるなら原文→提案で許可(standing:無断で原稿を変えない)。SITE_EDIT_WORKFLOW 配下。
- **残るゲート**: 依頼外なら編集の承認 + 公開。依頼済みなら公開のみ。

### E. favicon 一式の生成(資産・Bash が正解の側)
- **生**: `magick $S/head_sq.png -resize 16x16 ... $D/favicon-16x16.png`(16/32/180・ico)+ `magick identify` + `for f: curl -s .../$f`
- **引き金**: `curl`(ask)。magick は ask/deny に無く止まらない。
- **クラス**: 資産。**画像のネイティブツールは無いので magick-in-Bash が正しい**(「Edit を使え」は当てはまらない)。
- **正しい形**: `make_favicons.sh <src> <dest>`(値引数・固定リテラル)に確認まで畳む。レビュー成果物は diff でなく**拡大画像/スクショ**(standing「見た目はローカル+スクショで OK をもらってから staging」)。
- **残るゲート**: 見た目 OK + 公開。

### F. デプロイ着地の検証(ローカル vs staging)
- **生**: `ssh supercom-web1-stg 'curl -s -H "Host: thinkxinc.com" http://localhost:8005/products/KOBITO | grep icon; git log --oneline -1; shasum -a 256 favicon.*; grep ... nginx.conf'; echo ---; shasum -a 256 favicon.*`(ローカル)
- **引き金**: `ssh`(ask)。
- **クラス**: 観測(書き込みゼロ・両側読み取り。5 例中もっとも純粋)。
- **正しい形**: 新規 `verify_deploy.py <site> <path>`。既存の acceptance-sweep(ルート照合)/ check_request_path(疎通)に無い「バイト同一性でデプロイ着地を確認」を埋める。両側 shasum を突き合わせて **OK/MISMATCH** を出す(hex 2 列を人間に目視させない)。
- **残るゲート**: なし。

### G. デプロイ検証の縮小版(F の部分集合)
- **生**: `ssh supercom-web1-stg 'git -C /src/thinkx-system log --oneline -1; cd .../KOBITO && shasum -a 256 favicon.*'`
- **引き金**: `ssh`(ask)。
- **クラス**: 観測。
- **正しい形**: F と同じ `verify_deploy.py` に含める。
- **残るゲート**: なし。

### H. ブラウザの localhost サイト許可(別系統)
- **生**: 「Claude in Chrome wants to wait on 127.0.0.1:5000 / Allow all actions on 127.0.0.1:5000 for this session」
- **引き金**: settings ではなく **Chrome 拡張のサイト許可**(別システム)。
- **クラス**: 観測(自分の dev サーバー)。
- **正しい形**: 拡張の設定 → Permissions → 「Always allow actions on this site」で恒久許可(拡張アイコン→三点→Extension settings→Permissions の「Your approved sites」で管理・取消可)。settings/フック/スクリプトでは触れない。
- **残るゲート**: なし(localhost の dev のみ)。

### I. git add && git commit(複数行メッセージ)
- **生**: `git add X && git commit -q -m "件名\n\n本文...\n\nCo-Authored-By: ..."`
- **引き金**: allow に `Bash(git commit:*)` があるのに止まる。**メッセージの改行が区切りとして解釈され**、2 行目以降が未知の断片になって allow マッチが崩れる(実測 12.8 秒 = プロンプト)。
- **クラス**: 変更(ただし非破壊・可逆)。
- **正しい形**: PreToolUse フックで git add/commit を allow 判定(メッセージ内容に依存しない)。暫定策はメッセージ 1 行化 or `-m` 複数回。force push 等は deny のまま(deny はフックより強い)。
- **残るゲート**: なし(可逆)。

### J. WebFetch のドメイン
- **生**: `WebFetch(url: https://support.claude.com/...)` が新ドメインごとに承認。
- **引き金**: ドメイン未許可。
- **クラス**: 観測(信頼済みサイトの読み取り)。
- **正しい形**: `WebFetch(domain:*.host)` を allow に足す(apex は別に足す)、または承認済みファミリを記録して allow を返すフック。ask はフックの allow に勝つが WebFetch には ask を置いていないので allow で効く。
- **残るゲート**: なし(信頼済みのみ)。

### K. terraform apply の -auto-approve 全損事故(変更系の反例・最重要)
- **生**: `add_current_office_ip.sh`(内部で `terraform apply -auto-approve` を prod/staging 両 env に実行)。
- **引き金**: 本来 ask の `terraform apply` を **-auto-approve で回避していた**ため承認が出ず、IP 追加と無関係の AMI 追従差分(`data.aws_ami most_recent` の ForceNew)が同乗して **prod/staging 全 4 台を破壊再作成**(infra/findings.md 2026-08-06)。
- **クラス**: 変更(不可逆・破壊)。
- **正しい形**: 変更系は生 terraform でなくラッパー `terraform_apply.sh`(plan 全件提示 → yes → 実行)。**-auto-approve を作らない**。承認を「消す」でなく「残す」対象。
- **残るゲート**: apply/destroy の承認(人間)。削減対象ではない。
- **教訓**: これが「変更系は減らさない」の実証。変更系を auto-approve にすると危険な差分も無承認で通る。無承認化の議論は必ずこの反例と対で持つ。

### L. git push -u origin <branch>(push 規約)
- **生**: `git push -u origin 2026refactor`(CLAUDE.md の全リポジトリ統一 push 形)。
- **引き金**: base settings は `git push origin:*` と bare `git push` を allow するが、**`-u origin` は `git push origin` に前置一致しない**ため止まる。
- **クラス**: 変更(ただし非保護ブランチへの push は日常。force は別途 deny 済み)。
- **正しい形**: project settings の allow に `Bash(git push -u origin:*)` を足す(force 系は deny が勝つので安全)。現に `settings.local.json` に `Bash(git push *)` が追記済み = 実際に承認が出た証跡。project settings へ昇格候補。
- **残るゲート**: なし(非保護ブランチ)。force push は deny のまま。

### M. index.html をテンプレート+base64 資産から生成し、ローカルのモックで確認
- **生**: `python3 - "$S" <<'EOF' ...template 置換... write infra/claude_connect/index.html EOF; (lsof -i :8008 -sTCP:LISTEN -t | xargs -r kill); nohup python3 "$S/mock_server.py" ... &; curl -s http://127.0.0.1:8008/connect/deploy`
- **引き金**: `curl`(localhost)。python3 / lsof / xargs / kill / nohup は ask/deny に無く止まらない。
- **クラス**: 生成(build)+ ローカルのプロセス管理 + 観測。手編集でなくテンプレート展開の生成物。
- **正しい形**: インライン heredoc でなくレビュー済みの build スクリプト(例 `build_index.py`)にする(事例 C/E と同じ。生成物は固定スクリプト、確認まで畳む)。localhost curl と mock の起動/停止もそのスクリプトに固定リテラルで入れる。対象ポート(8008)は固定し、任意 PID を kill する形にしない(偽装防止と同じ原則)。
- **残るゲート**: 生成物の見た目 OK(claude_connect ページ)+ 公開。ローカルの mock 起動/kill は可逆なので承認不要。
- **メモ**: ローカルのテスト用プロセス管理(固定ポートの mock を落として立て直す)は可逆・局所なので安全クラス。ただし固定ポート限定で、任意 PID を引数で受けない。

### Watch list(ask 系だが v1 では実例が出ていない)
出たら同書式で追記する。想像で先に書かない(corpus は実例のみ)。
- `brew install`(依存導入)= 変更(環境)。残す寄り。
- `git restore`(作業ツリー復元)= 可逆だがレビュー価値あり。
- `git tag -d`(タグ削除)= 完遂タグを動かさない規約(D-24)と衝突しうる。要注意。
- `git submodule deinit` = Track Q の submodule 制約と絡む。要注意。

---

## 蒸留メモ(パターン)

- **承認の引き金の実体は 2 つに集約される**: (1) ask 語(`ssh` / `curl`)が可視コマンドの先頭にある、(2) allow ルールが内容(複数行メッセージ・本文中の区切り記号)で崩れる。どちらもスクリプト/フックに畳むと消える。
- **畳む正当性は「相手が安全か」で決まる**。localhost GET・読み取り観測は畳んでよい。外部・本番・副作用は生のまま承認を残す。全 curl・全 ssh を無条件に畳むと、ask が止めるはずの外部・本番のコマンドまで無承認で通る。
- **同型でも中身で扱いが変わる**(C=整形 vs D=改題)。形でなく相手とレビュー成果物で判断。
- **変更系は削減しない**: 事例 K が実証。terraform apply/destroy・本番反映・send-keys 等は auto-approve にしない。承認を消してよいのは「観測」と「依頼済みの可逆な編集」まで。
- **昇格の入口**: 同型を 3 回書いたら固定スクリプトのサブコマンド化(判定基準側にも記載)。
- **収録済みの承認引き金(v1 時点)**: ssh(A/B/F/G)・curl(C/D/E)・複数行 git commit(I)・WebFetch ドメイン(J)・Chrome 拡張のサイト許可(H・別系統)・terraform -auto-approve の反例(K)・git push -u origin(L)。未観測は Watch list。

---

## 判定方式の割り当て(2026-09-06 確定)

**前提(確定)**: settings の前置一致だけでは不足。**settings / hook 判定 / 固定 wrapper の 3 層を使い分けるのが必須。**

割り当ては 3 問で決まる:
1. settings の前置一致で書けるか。
2. 実行時にコマンドを安全に分類できるか(文法が綺麗で、危険な形を数え上げられるか)。
3. 頻度が高く習慣的か(高いと、毎回 wrapper を使わせる規律が崩れて生コマンドが漏れる)。

| 対象 | settings で書ける | 分類が安全 | 頻度 | 割り当て |
|---|---|---|---|---|
| git add | 可 | — | 高 | **settings** |
| WebFetch ドメイン | 可(`domain:*.host`) | — | — | **settings** |
| git commit(複数行・トレーラ) | 不可(改行が前置一致を壊す) | 安全 | 最高 | **hook 判定** |
| git push(非破壊) | 不可(フラグ位置が任意) | 安全 | 高 | **hook 判定** |
| curl(localhost) | 不可(host/method を書けない) | 危険(localhost 偽装) | — | **固定 wrapper** |
| ssh(観測) | 不可 | 不能(引数の中身が不透明) | — | **固定 wrapper / forced-command** |
| terraform apply/destroy | — | — | 低 | ゲート維持(自動承認しない) |
| 編集(C/D/E/M の生成部) | — | — | — | Edit / build script(Bash でない) |
| browser localhost(H) | — | — | — | Chrome 拡張(別系統) |

- 判定(hook)が要るのは「実行時分類が**安全かつ有益**」な交点 = **git だけ**。git は settings で書けず、頻度が最高で wrapper 規律が崩れ、しかし文法が綺麗で判定が安全、という唯一の場所。
- curl/ssh は分類が危険/不能なので、判定でなく**構築による安全(固定 wrapper)**。任意コマンドを安全分類することが原理的に危ういため。
- deny の床(force push・rm・sudo・鍵/tfstate 等)は全層で維持。hook も wrapper も、この床の上で承認を足すだけ。
- 実装: settings = 既存 allow / hook = `hooks/check_git_command.py`(git commit・push) / wrapper = `infra/scripts/stg.py` 等(curl・ssh 観測)。

---

## 状態と次の一手(2026-09-06 セッション終了時)

- **v1 実装・コミット/push 済み(96ee870)**: `hooks/check_git_command.py`(git 判定)/ 本 corpus / `docs/DEPLOY_APPROVAL_LEVELS.md`(判定基準・安全モデル・オーナー指示・hooks ブロック説明)/ `infra/docs/STG_OBSERVE_PLAN.md`。
- **オーナーが `.claude/settings.json` の hooks を置き換え済み**(PreToolUse に `check_git_command.py` を登録)。反映はセッション再起動時。
- **次の一手**:
  1. 動作確認(再起動後): 複数行コミットで承認が出ない / `git push --force` は deny で止まる / `git add x && curl <外部>` は curl でプロンプト。
  2. 確認できたら v2 へ。curl/ssh は固定 wrapper 層(`infra/scripts/stg.py` 済み、`verify_deploy.py` は事例 F/G がもう一度出たら昇格)。
  3. 新しい承認事例は `docs/approval_cases_v2.md` に貯める。v1 は構築材料としてここで凍結し archive 候補。
- **未着手**: WebFetch ドメイン記憶(settings の domain allow か記憶フック)/ curl localhost の wrapper 化(必要になったら)。
