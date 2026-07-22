<!-- 配置: thinkx-system/monorepo/citywalk/findings.md -->
<!-- findings はリポジトリ配下に置く(各サイトの状態はリポに帰属する)。横断台帳(M-F 系)は monorepo/docs 側。 -->

# findings — citywalk 再構築(Phase 4c)

記録規則: 「ファイル:行 / 事実 / 発見項目ID」。解釈を書かない。修正しない(Phase 3 の入力・D-20)。
Security exception(D-22)はここに書かず即停止・人間へ報告。

## 前提(人間の裁定の転記欄。C-0a で埋める)

- §7-1 旧 public リポの秘匿情報対応: (未裁定 / GCP キーはリファラ制限が人間の宿題)
- §7-3 purchase: (未裁定 — 裁定まで C-4g 着手禁止)
- §7-4 データ移行: (未裁定 — 裁定まで C-3 着手禁止。auth/docs D-13 は「初版は新規のみ・移行なし」)
- §7-6 スタイル統一(推奨 less): (未裁定)
- §7-7 signin/signup の auth 導線化: (未裁定)
- (§7-2 iOS は計画 §1.0「未稼働」により解決済み。§7-5 リポ名は citywalk で確定。)

## 秘密の裁定記録(C-0a。値は書かない)

- (A) Basic 認証資格情報 → redact 済み: `views/business.py`(該当箇所)、`api/items.py`(該当箇所)。
- (B) クライアント配信型 GCP/Google Maps キー → 裁定により残置(本物の地図を UI オラクルで出すため)。
  所在: `views/src/ECMA/business/appconfig.js`・`templates/business/pages/{createguide,signup}.html`・
  分析ノート2本。**要リファラ/API 制限(人間の宿題)。**
- (C) クライアント非配信・再構築後 config 化される鍵 → redact 済み: `scripts/main.py` の Flask secret_key。
- 一般規則(既知裁定済みクラス): (A) redact /(B)残置 /(C)redact。これ以外の実秘密は D-22 で停止・報告。

## auth OIDC 仕様の前提(v3.0 で確定・C-5 の入力)

- auth は OIDC Authorization Code Flow + PKCE(S256)。正本は `monorepo/auth/docs/`(00〜05)。
- citywalk は client(RP)として実装: ClientTransactionStore / AuthClient / IDTokenVerifier /
  ServicePrincipal + `/auth/signin`・`/auth/callback`・`/v1/sessions/revoke`・logout(3種)。
- 新規依存 PyJWT(ID Token 検証)。identity は ServicePrincipal(issuer, subject) → local_user_id。
- auth/docs D-13「初版は新規のみ・移行なし・突合キーにメール不可・複合ユニーク必須」。§7-4 に連動。

## C-0c デモ動画(ground truth)

- オーナー提供 createguide デモ動画(135秒・1490×856・主要アニメーションを全て含む・往時の本番の記録)を
  `tests/golden/ui_legacy/ground_truth/` に Git LFS で配置。`.gitattributes` の `*.mov` 規則により
  Git index は LFS pointer(OID/サイズのみ)を保持する。判定はアニメーションフロー一貫性
  (ピクセル一致でない・地図タイルの経時変化は許容)。オーナー目視承認が C-1 への関門。
- `web-server/tests/golden/ui_legacy/ground_truth/createguideviewdemo.mov:0.0-8.0秒` / 初期フォームからコンテンツ一覧・地図分割表示、地図スポット選択、左編集パネル開閉を確認 / C-0c
- `web-server/tests/golden/ui_legacy/ground_truth/createguideviewdemo.mov:12.0-30.0秒` / 地図スポット選択とコンテンツ編集状態、左編集パネル開閉の反復を確認 / C-0c
- `web-server/tests/golden/ui_legacy/ground_truth/createguideviewdemo.mov:32.0-38.0秒` / 地図パン・ズームとフォーム選択メニューの開閉を確認 / C-0c
- `web-server/tests/golden/ui_legacy/ground_truth/createguideviewdemo.mov:59.0-68.0秒` / 地図のパン・ズーム・再中心化とフォーム編集状態への遷移を確認 / C-0c
- `web-server/tests/golden/ui_legacy/ground_truth/createguideviewdemo.mov:78.0-130.0秒` / 翻訳候補パネルのスライド展開・スクロール・候補選択・閉鎖と翻訳済みフォーム反映を確認 / C-0c

## 計画作成時の発見(2026-07-07。計画 §1.5 から転記)

- F-1: www/server/application/views/node_modules / node_modules がコミットされている / 計画§1.5
- F-2: www/requirements.txt / Jupyter・ipython・notebook 系が web 依存と混在(appnope 等 macOS 固有物含む) / 計画§1.5
- F-3: scripts/helpers/ / date_utils.py と dateutils.py が並存 / 計画§1.5
- F-4: scripts/main.py:58-61 / @app.errorhandler(400) の本体が pass(TODO コメント付き) / 計画§1.5
- F-5: scripts/analytics_notes/*.ipynb / 長崎実証の分析ノートが旧 public リポジトリに存在(出力セルの精査は人間) / 計画§1.5
- F-6: scripts/libcommon(submodule) / 旧世代 libcommon(session/mongobase/enumlocale/modelbase/logger)で現行 v2.1.0 と別系統 / 計画§1.5
- F-7: views/src/ECMA/heritage/ / coffee ソースとコンパイル済み js が二重コミット / 計画§1.5
- F-8: views/templates/mails/ / user 系と organization 系のメールテンプレートが二重化 / 計画§1.5

## 実行中の発見(実行者が追記)

- `git:ba5acaf51dbe37cbc14e18582509c78343a1f563` / 畳み込み前コミット `C-0a: legacy 取り込み・Basic認証 redact・GCPキー裁定残置・台帳凍結` / M-F8
- `git:dacdb4e8ba71b5491e79a7ba093fe85cbb98e4da` / 畳み込み前コミット `C-0b: 規範配置と findings 初期化` / M-F8
- `legacy/www/server/application/scripts/main.py:100` / 同型の Flask session 署名鍵直書きを追加検出し、裁定(C)により値を `<REDACTED>` 化 / C-0a
- `web-server/tests/extract_ground_truth_keyframes.sh:12` / manifest を標準入力で読む初版では FFmpeg が入力を消費して出力名が欠損したため、専用 file descriptor と単一 FFmpeg 選択式へ置換 / D-21
- `docs/ROADMAP.md:39` / Phase 4c の規範表記が v2.0 のままで、`citywalk/refactor_plan.md` ヘッダ v3.0 と不一致 / D-21
- `docs/CITYWALK_TRACK.md:39` / 合格条件が screenshot+jsdom の二層表記のままで、`citywalk/refactor_plan.md` C-0c の ground truth+3層表記と不一致 / D-21
- `web-server/requirements-legacy-ui.txt:14,18` / legacy Redis 3.5.3 維持・試験用 fakeredis を互換メタデータ確認済みの 1.x (`1.7.1`) へ最小置換 / D-21
- `legacy/www/server/application/views/templates/business/main.html:7,19` / 確定取り込み元 SHA の tree に存在しない `/js/business/helpers/session.js` と `/js/business/main.js` を参照 / D-21
- `legacy/www/server/application/scripts/libcommon:1` / 取り込み元では commit `98e87376e716e82263ae5ff8cfad7dfea40a02cf` の gitlinkだが、legacy 配下は空ディレクトリ / D-21
- `web-server/tests/golden/ui_legacy/motion/:1` / 旧実ブラウザ環境を起動できていないためローカル再現フレーム列・ground truth 照合は未作成 / C-0c
- `legacy/.gitignore:27-28` / `views/js/*` は旧 repo で ignore 対象、確定 SHA の `git ls-tree` に `js/business/{helpers/session,main}.js` は存在せず force-add 追跡資産ではない / D-21-JS-a
- `legacy/www/server/application/views/package.json:8` / build は `src/ECMA` 全体を Babel で `js/` へ生成するが、確定 SHA の source tree に `business/helpers/session.js` と `business/main.js` は存在せず当該2本は再生成不能 / D-21-JS-b
- `git:0a63bcee55772e19d87ec0234be4947a56a48059` / `src/ECMA/business/main.js` を削除、削除直前の本体は `console.debug('run main.js')` のみ、template の `/js/business/main.js` 参照は残存 / D-21-JS-c
- `git:283ec59309085436dfb392a1d3c92de89ef70cb0` / `/js/business/helpers/session.js` 参照を追加した同一 commit に当該 source/blob は存在せず、session 実体は `appconfig.js` の `app.session = {}` と新設 `models/session_model.js` / D-21-JS-c
- `legacy/www/server/application/views/src/ECMA/business/{effects.js,view_components,view_controllers}:1` / createguide の transition・setTimeout・Web Animations 実装は欠落2本と別の追跡 source 群に存在 / D-21-JS-c
- `legacy/www/server/application/views/templates/business/main.html:7,19` / オーナー裁定により (c) を許容、既知の無害な404として legacy 無変更、アニメーションは `effects.js`・`view_components/*`・`view_controllers/*` が担う / D-21-JS-c
- `web-server/:1` / C-6 の新実装にはデッドな `/js/business/helpers/session.js`・`/js/business/main.js` 参照を持ち込まない / C-6
- `web-server/tests/golden/ui_legacy/ground_truth/animation_segments.tsv:S19-S21` / 翻訳パネル実座標 `x=410..659` を可視領域とし、当該区間の地図マスク開始を `x=660` へ変更して差分を再計測 / C-0c
- `web-server/tests/golden/ui_legacy/ground_truth/motion_reference/:1` / 21区間を裁定fpsで計2,240枚・745×428 PNGへ抽出、PNG自体は無マスク、比較マスクは manifest に分離 / C-0c
- `.gitattributes:11` / 高密度PNG 582MBを通常Git blob化しないため `motion_reference/**/*.png` のみ Git LFS管理 / C-0c
- `git:981db15e36ee61f079eef76676202a6edf881f55` / `docs(infra)` commit が当時未追跡だった citywalk C-0c 試験資産を同時に追跡し、その後 release に含まれた / D-49
- `legacy/www/server/application/scripts/libcommon/enumlocale.py:144` / `is_valid_value` に `@classmethod` が無く signup/settings handler が TypeError になるため、試験ランタイム内で documented API を復元 / D-21
- `legacy/www/server/application/scripts/views/business.py:99` / `/business/signin` が参照する `templates/business/signin.html` は確定取り込み元に存在せず 500 になるため、空画面 fixture を UI 基準にしない / C-0c
- `legacy/www/server/application/views/templates/business/pages/{signup,createguide}.html:1` / 実ブラウザ起動時に Google Maps JavaScript API が `ExpiredKeyMapError` を返し、地図中心・パン・ズーム・配置 motion を生成できない / C-0c
- `web-server/tests/legacy_ui_server.py:1` / 旧 business blueprint を Python 3.10 互換 shim と旧 libcommon snapshot 上で実起動し、fixture の Jinja 直レンダリングを廃止 / C-0c
- `web-server/tests/legacy_ui_server.py:1` / `CITYWALK_GOOGLE_MAPS_API_KEY` を実行時注入し、旧固定キーの `ExpiredKeyMapError` を解消。キー値は成果物・診断へ保存しない / C-0c
- `web-server/tests/ui/ui_legacy.test.js:1` / 旧 ECMA 47本の Babel build、実 Maps の load/center/zoom 検証、desktop の可視地図領域限定マスクを通した実ブラウザ試験が green / C-0c
- `web-server/tests/golden/ui_legacy/business_createguide_{desktop,mobile}.png:1` / 修正後の静止画でコンテンツ4件と左UIを保持し、desktop は右側の可変地図領域のみマスク、mobile はマスクなし / C-0c
- `web-server/tests/golden/ui_legacy/motion_contract.json:1` / 旧実装から content選択、edit panel閉鎖、translation panel閉鎖の順序・duration・stagger・軌跡を機械可読化 / C-0c
- `web-server/tests/ui/capture_legacy_motion.js:1` / 1490×856実Chromeで content選択、edit panel閉鎖、地図pan/zoomを操作し、目視用WebMとrequestAnimationFrame座標列を `motion/` へ出力する収録ハーネスを追加 / C-0c
- `web-server/tests/golden/ui_legacy/motion/README.md:1` / translation panelの実サービス依存部分は未収録であり、挙動を捏造せず残件として明記 / C-0c
- `web-server/tests/build_motion_review.sh:1` / ground truthを左、ローカル実ブラウザ収録を右へ745×428ずつ配置した1490×428 H.264並列目視出力を決定的に生成 / C-0c
- `web-server/tests/ui/validate_motion_trace.js:1` / 収録traceの必須3 flow、時刻単調増加、cell軌跡、edit panel閉鎖、map center変化・zoom +1を契約照合 / C-0c
- `web-server/tests/golden/ui_legacy/motion/alignment.tsv:1` / local 3 flowをground truth S02–S14へ対応付け、S19–S21はtranslation service未再現として別途blockedを保持 / C-0c
- `web-server/tests/ui/capture_legacy_motion.js:1` / 各local flowの操作中だけCDP PNG screencastを収録し、使用フレーム名とbrowser timestampをtraceへ固定 / C-0c
- `web-server/tests/build_motion_review.sh:1` / local flowを対応する代表ground truth S02/S04/S10と個別に並列化し、無関係な135秒全体比較を回避 / C-0c
- `legacy/www/server/application/views/src/ECMA/business/helpers/translate.js:1` / オーナー裁定により廃止済みbrowser-side DeepL endpoint・認証値・外部fetchを除去し、外部送信しないfail-closed互換面へ置換 / C-0c
- `web-server/tests/ui/motion_contract.test.js:1` / legacy translation helperへのDeepL endpoint・認証parameter・fetch再混入を拒否 / C-0c
- `web-server/tests/fixtures/legacy_translation.js:1` / production demo S19の11言語・表示順を根拠に、外部通信なしのtest-only translation completion fixtureを固定 / C-0c
- `web-server/tests/legacy_ui_server.py:1` / legacy sourceの廃止済み翻訳面はfail-closedのまま維持し、C-0c実ブラウザだけfixtureを配信 / C-0c
- `legacy/www/server/application/views/src/ECMA/business/view_controllers/createguide_view_controller.js:149` / 選択contentを表示用へ設定する一方editable clone設定が欠落し、入力時に`isEmpty`を呼べない。ground truthと同ファイル内`_startEditContent`を根拠に試験runtimeだけ復元 / D-21
- `web-server/tests/ui/capture_legacy_motion.js:1` / demo由来入力と11言語fixtureでS19 population、S20 smooth scrollのPNG列・rAF traceを収録対象へ追加 / C-0c
- `legacy/www/server/application/views/src/ECMA/business/view_components/translate_results_table_view.js:365` / cell clickは`onselected` state設定のみで、S21の選択反映・closeを行うobserverが確定source内に存在しないため当該flowはblockedを維持 / D-21
