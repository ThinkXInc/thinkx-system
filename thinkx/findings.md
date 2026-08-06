# thinkx findings(S トラック / Phase 2.5)

規範: `thinkx/refactor_plan.md`(静的サイト群 vendoring カットオーバー計画 v1.1)。
本ファイルは thinkx リポジトリ直下(計画 大原則3)。Security exception は即停止・報告(D-22)。

---

## S-0a 前提ゲート(2026-07-07 実測・確認のみ)

- `git -C libcommon tag -l v2.0.0` → `v2.0.0`(存在)。
- `libcommon/scripts/bake.sh` 存在。
- tree_sha256 再算出一致: `bash bake.sh v2.0.0 <tmp>` → `3359309a30a392a75a97b3fad594569487cb07068f770877202de3096fb57cf0`
  = 計画パラメータ(Q-6 実測値)と完全一致。
- libcommon ゲート: `ruff check .` = All checks passed / `pyright` = 0 errors(5 warnings: TypeVar 用法・新版通知のみ)。
- settings.json スコープ切替: 人間が適用済み(deny を各サイト `web-server/libcommon/**` のみへ限定)。

### F-S1(記録・別トラック): libcommon の bare `pytest` は緑でない
- `.venv/bin/pytest`(引数なし)で collection error 3件:
  - `tests/modelbase_test.py` / `tests/mongobase_test.py` → `ModuleNotFoundError: No module named 'nose'`
  - `vector_database/test_vector_database.py` → `ModuleNotFoundError: No module named 'torch'`
- いずれもリファクタ対象外の旧世代テストモジュール(消えた optional 依存 nose/torch を import)。
  libcommon 計画の setup が入れる依存は `pytest fakeredis flask pydantic …` のみで nose/torch を含まない。
- 判断: v2.0.0 デリバラブルの健全性は tag + tree_sha256 一致で機械証明済み。サイトが消費する
  [凍結]面(logger/color/validator/locale/language/web.http_errors・http_successes・
  validation_errors/mail/discord)とも無関係。**別トラック(libcommon)の遺物テスト債務**であり
  Phase 2.5 の前提充足を妨げないと判断して S-0b へ進行。libcommon 側で解消すべき事項として記録。

---

## S-0b スモークハーネス(2026-07-07)

### 消費面の実測(計画 大原則2 の裏取り)
- thinkx main.py / flask_helper.py / mails/send_mail.py が消費する libcommon:
  `discord`(send_discord)・`language`・`locale`・`logger`・`color`・`validator`・
  `web.validation_errors`・`web.http_errors`・`web.http_successes`・`mail`。
  flask_helpers / session は不使用(計画通り [凍結]面のみ)。
- ピン submodule commit `7b15ee6…`(thinkx)は上記モジュールを v2.0.0 と同一に保持
  (pinned には削除予定の deprecated: `web/[DEPRECATE]api_errors.py` `web/api_response_v1.py`
  `web/errors_v1.py` が余分に在るが、サイトは import しない)。→ S-1 カットオーバーでゴールデン
  不変になるはず。

### import 時の外部依存(注入で遮断)
- `libcommon.locale` は `from config import Config`(ホスト config を読む現行仕様)→
  conftest が `sys.modules['config'] = config_test` を main import 前に注入して解決。
- `libcommon.mail.Mail()` は mails/send_mail.py の import 時に生成され `boto3.client('ses')` を
  呼ぶ → conftest で boto3.client/resource を MagicMock 化(実 AWS I/O 遮断)。
- 本サイトは mongo / redis / session を import 時に接続しない(quantz Q-1 の mongomock/fakeredis
  差し込みは不要)。→ conftest は config 注入 + boto3 mock のみ。

### 環境(計画に venv 項目が無いため実行者が決定・記録)
- S トラック専用 venv: `<workspace>/.s-track-venv`(ワークスペース直下=git 管理外)。
- 版は libcommon v2.0.0 の検証環境 `.venv` に合わせる: Flask 3.1.0 / Jinja2 3.1.6 /
  Werkzeug 3.1.8 / pydantic 2.10.4。加えて boto3 1.34.122(mail)/ requests 2.32.5(discord)/
  python-dotenv 1.0.1 / pytest 8.3.4。
  - 注: サイト requirements.txt は Flask 0.12.2 の旧ピンだが py3.10 で導入困難かつ本計画は
    「同一 env で S-0b 取得・S-1 検証」すればスワップ回帰オラクルとして妥当なため、v2.0.0 検証環境に
    揃えた。本番デプロイ版の整合は Phase 2.5 の範囲外(サイト無変更)。
- submodule はローカル libcommon clone からオフライン初期化:
  `git -C thinkx -c protocol.file.allow=always -c submodule.web-server/libcommon.url=<local> \
   submodule update --init web-server/libcommon`(ネット/ssh 不要)。playbooks submodule は触らない。

### ゴールデン
- `from main import app` 成功(test_app_imports)。
- GET ルート sweep 56件を `tests/golden/route_sweep.json` に凍結(test_route_sweep)。
  200/302/404/500 を現状のまま記録(500 は test env でのロケール/動的コンテンツ欠落による現行挙動。
  回帰オラクルとして凍結、S-1 で不変を要求)。truetechjapan / nntm アセットサイトのルートを含む。
- 実行: `.s-track-venv/bin/python -m pytest tests/test_app_imports.py tests/test_route_sweep.py`

---

## S-1 thinkx カットオーバー(2026-07-07)

- `git submodule deinit -f web-server/libcommon` → `git rm -f web-server/libcommon`
  (gitlink 除去 + .gitmodules から libcommon 節削除。**playbooks 節は残存**)。
- `bash libcommon/scripts/bake.sh v2.0.0 thinkx/web-server/` → 実物コピー + VERSION 生成。
- VERSION tree_sha256 = `3359309a…cf0` = S-0a パラメータと一致(bake 出力 + 独立再算出
  `find -not __pycache__ -not *.pyc -not VERSION | sort | xargs shasum | shasum` の両方で MATCH)。
- 焼き込んだ `libcommon/.gitignore` が無視するのは `__pycache__/*.pyc`(pytest が生成した一時物)のみ
  = bake の hash 除外対象と一致。実ソース129ファイルは全て tracked(pyc 混入なし)。
- 検証: `from main import app` green / ルートゴールデン(56件)不変 / git status は
  {M .gitmodules, D gitlink, A 129 実ファイル} のみで想定外差分なし。

## S-2 thinkx デプロイ経路の submodule 依存検査(2026-07-07)

- 検査対象: `deploy.sh` / thinkx 直下スクリプト / CI 設定 / 追跡ファイル全体
  (`git grep -E 'submodule|recurse-submodules'`、web-server/libcommon と本計画 docs は除外)。
- 結果: **libcommon 由来の `git submodule update` / `--recurse-submodules` は0件**。
  - `deploy.sh` は `ansible-playbook -i playbooks/thinkx playbooks/thinkx.yml` のみ(submodule 取得なし)。
  - CI 設定ファイルは未追跡(`.github/` 等なし)。
  - `.gitmodules` に残るのは playbooks 節のみ(意図通り)。libcommon 分は S-1 で除去済みのため
    将来の `submodule update` でも libcommon は取得されない。
- **人間確認事項(F-S2)**: `playbooks` submodule(commit `38bf25a…`・別リポ・本計画対象外)は
  未初期化 + ネットワーク遮断のためオフライン検査不可。playbooks 内に旧 `web-server/libcommon`
  submodule パスへの参照や `git submodule update --recurse` があれば、その libcommon 取得ステップは
  不要になっている(playbooks 自体の取得は残す)。playbooks 原本での確認は人間判断。
- deploy 経路コードの変更は無し(計画 S-2「変更があった場合のみコミット」に該当せず。本記録のみ)。

---

## E-1 truetechjapan 受賞企業ページ新設(2026-07-19)

計画外の追加作業(オーナー直接指示)。ROADMAP の管轄としては E トラック
(SITE_EDIT_WORKFLOW.md)の領域だが、同文書は「カットオーバー前は発効しない」ため
本セッションはローカル実装 + ローカル検証までで、staging/PR フローには乗せていない。

### 実装
- ルート: `/truetechjapan/award/<company_key>` と `/truetechjapan/<lang>/award/<company_key>`。
  nginx(truetechjapan.com server block)の `rewrite ^/(?!truetechjapan)(.*)$ /truetechjapan/$1`
  により公開 URL は **`https://truetechjapan.com/award/thinkx`**(および `/ja/`・`/en/` 前置)。
  ID は振らず、企業キー(= JSON ファイル名)がそのまま URL になる。
- データ: `views/templates/truetechjapan/award_companies/<key>.json`(1企業=1ファイル)。
- テンプレート: `views/templates/truetechjapan/award_company_page.html`(全企業で共通)。
- スタイル: `views/src/less/truetechjapan/award_company.less`(main.less に import)。
- レイアウトの典拠: `views/templates/truetechjapan/sample/受賞企業ページサンプル.pdf`。
  PDF の斜線ボックスとピンク文字は配布用の記入指示であり、サイトには出さない(オーナー指示)。

### F-E1(既存の失敗・本変更とは無関係): route_sweep ゴールデンが古い
- 本作業の着手前時点で `tests/test_route_sweep.py` は既に FAIL していた。
  差分は `/filedrop: golden=None actual=200` の1件のみ。`/filedrop` ルートは main.py に
  存在するが S-0b でゴールデンを凍結した後に追加されたと見られる。
- 本セッションで `/filedrop: 200` をゴールデンへ明示追記した(黙った再生成ではなく、
  既存ルートの取りこぼしの補正として記録)。

### F-E2: pytest が requirements.txt に無い
- `tests/` は pytest 前提だが `requirements.txt`(本番ピン)にも venv にも pytest が無く、
  `python -m pytest` が実行できなかった。本セッションで `venv` に pytest を追加導入した
  (requirements.txt は本番依存のため変更していない)。dev 依存の管理方法は要判断。

### F-E3: config_test に SRC_ROOT を追加
- 受賞企業 JSON の探索に `Config.SRC_ROOT` を使ったところ、テスト用 Config に同キーが
  無く AttributeError。conftest の設計(「欠落は顕在化させ反復で補う」)に従い
  `tests/config_test.py` へ `SRC_ROOT` を追加した。本番 config.py は未変更。

### F-E4(要判断): 認定シール画像の解像度
- ページ右上の Best Tech 100 シールは既存の `img/truetechjapan/header/header-logo-sp.png`
  (113x113)を `img/truetechjapan/award_companies/best-tech-100-seal.png` として複製して使用。
  Retina では甘い。年号入りの高解像度版(`top/top-logo-v2.png` 内)は「2025」が焼き込まれており
  2026 受賞ページには使えない。年号なし高解像度シールの支給が望ましい。

### F-E5(要判断): 受賞企業データが日本語のみ
- `award_companies/*.json` は company_name / business / award_reasons が日本語単一値。
  ラベル(受賞年・創業者・事業内容 等)は locale 化したが、企業固有の値は
  `/en/award/<key>` でも日本語のまま表示される。英語版を出す場合はデータ構造の
  多言語化(値を {ja, en} にする)が必要。

### F-E6(要判断): インタビュー節の扱い
- `interview_url` が null の企業では **節ごと非表示**にした。PDF では見出し「インタビュー」が
  黒字で、その下にピンクの注記「インタビューをお申し込みの場合、インタビューページへの
  リンクが記載されます」がある。見出しだけ常時出す解釈も可能。現状は非表示。

### F-E7(既存・未修正): main.py の COMMON_LOCALES_ROOT が壊れている
- `COMMON_LOCALES_ROOT = join(abspath(__file__), 'libcommon/locales')` は `dirname()` 欠落で
  `.../main.py/libcommon/locales` を指す。現状どこからも参照されていないため実害なし。
  規約に反する既存コードを勝手に直さない方針(CLAUDE.md)により未修正・記録のみ。

---

## E-2 多言語化 + Augmented Communications 追加(2026-07-19)

- 企業固有の値(company_name / founders / business / award_reasons)を
  `{"ja": ..., "en": ...}` 構造に変更。`main.localize_award_company()` が lang で潰す。
  **訳が未供給(キー無し or 空)なら ja へフォールバック**する(企業から英訳が届く前でも
  ページを落とさないため)。tier / url / award_year / logo は言語非依存で対象外。
- `tier` を任意化。null の企業ではチップごと出さない。
- 配布用 PDF の実測(300dpi サンプリング)で判明したスタイル差を修正(オーナー指摘):
  - 受賞年 / 創業者ラベル: 直角・単色 `#f0d484`・黒の **font-weight 600**(高さ 30.5pt)
  - Top-Tier チップ: **別物**。角丸・グラデーション・文字色 `#b38e0c`(金茶)で
    高さ 12.5pt = ラベルの約 0.41 倍
- ティア + 認定シールは常に画面右上。スマホでは横に並ばないため `column-reverse` で
  社名の少し上・右寄せに配置(オーナー指示)。

### F-E8(要判断): 残り3社の tier が未供給
- Group 1 の enex に tier の記載があるのは ThinkX(Top-Tier)のみ。
  Augmented Communications / レボーン / Beam Technologies は未指定のため `null`
  (チップ非表示)で作成した。枠が決まり次第 JSON の `tier` を埋める。

### F-E9(解決済み): 創業者名の英語表記
- 五十嵐 俊治 のローマ字表記は公式サイト(augmented.jp)に記載が無く、読みが一意でない
  (Shunji / Toshiharu / Toshiji 等)。**人名を推測しない**方針で `founders.en` を空にし、
  /en でも日本語表記が出るようにした。
- 2026-07-20 オーナーより正式表記の supply: **Igarashi Toshiharu**(ご本人の署名表記。
  姓+名の順)。語順を westernize せずそのまま採用した。

### F-E10: award_year は 2026 と仮置き
- enex に受賞年の記載があるのは ThinkX のみ。同一コホートとみなし残りも 2026 とした。
  異なる場合は JSON の `award_year` を修正する。

### F-E11(要判断): 松岡広明 のローマ字表記
- 公式サイト(revorn.co.jp)に代表者のローマ字表記が見当たらない。F-E9 と同じ方針で
  推測せず `founders.en` を空にした(/en でも日本語表記)。正式表記の supply が必要。
- 社名英語表記は公式サイトの記載 **REVORN Co., Ltd** を採用。URL も同サイトの
  `https://www.revorn.co.jp`(enex に URL の記載が無かったため公式サイトで確認)。

---

## E-3 BEAM Technologies 追加(4社目・公開情報から収集)(2026-07-20)

企業から情報が届いていない唯一の社。オーナー指示で公式サイトから収集した。

- 指定 URL `https://beam-tec.jp/about` は `https://beam-tec.co.jp/about` へ 301。
  正URLは **beam-tec.co.jp**。

### 事業内容と受賞理由の食い違い(調査して解消)
- 受賞理由は「短波長の安全な Far-UVC を 1mW で出力する世界水準の技術」と述べるが、
  公式サイトの現事業は **宇宙空間の微小重力を使った化合物半導体(AlGaN)製造プラットフォーム**
  で、Far-UVC は出てこない。
- 追加調査の結果、Far-UVC は**創業チームの理研での研究実績**(「2022年に世界記録を達成した
  理研の Far-UVC LED の研究に携わり」)であり、現事業ではないと判明。矛盾ではない。
- したがって **事業内容には現事業(宇宙半導体製造)を書き、受賞理由は支給文のまま**とした。
  受賞理由を現事業に合わせて書き換えることはしていない(審査の文言は改変しない)。

### F-E12(要判断): ロゴが白抜きしか公開されていない
- 公式サイトが公開しているのは (1) 白抜きの BEAM ワードマーク(透過 PNG・1461x694)と
  (2) 黒地に白い「B」のファビコン(512x512)のみ。**白背景の本ページでは (1) は見えない**。
- ロゴの色を勝手に反転する(=他社ロゴの改変)ことは避け、**ロゴは無加工のまま暗パネルに
  載せる**方式にした。JSON の `logo.background: "dark"` で指定する汎用オプションとして実装
  (白抜きロゴしか無い企業が今後も出るため)。
- 望ましいのは企業から正式なロゴデータを受領すること。暫定対応である。

### F-E13(記録): 創業者ローマ字表記の語順が社ごとに揃っていない
- Igarashi Toshiharu / Matsuoka Hiroaki(オーナー supply・姓+名)に対し、
  BEAM の飯村氏は**公式サイトが自ら "Kazuki Iimura"(名+姓)と表記**している。
- 各人の自称表記を尊重してそのまま採用した。サイト全体で語順を統一する方針にするなら
  一括で決める必要がある。

### F-E14(事故): ビルド生成物を直接編集した(2026-07-21)

- **何が起きたか**: TrueTech の表示遅延(表示まで約6000ms)を直す際、
  `web-server/views/js/main.js` を直接編集した。同ファイルは `views/src/js/main.js` から
  babel が生成する**ビルド生成物**で `.gitignore` 済み(`thinkx/.gitignore:35`)。
  次のビルドで消える変更だった。`git status` に何も出ないことで気づき、
  `git check-ignore` で確定。`src/js/main.js` を直して babel で焼き直した。
- **必要な事実がどこにあったか(いずれも既存)**:
  - `docs/SITE_REQUIREMENTS.md` L17-19 —「views/src/js … babel/lessc で書き出される」
    「gitignoreに実生成物 views/js, views/css, views/video」
  - `thinkx/docs/受賞企業ページの作り方.md` §2-4 —「`css/main.css` は `.gitignore` 済み
    (ビルド生成物)」。ただし **lessc/CSS のみで babel/JS の記載は無い**。踏んだのは JS 側。
- **なぜ届かなかったか(配線の穴)**:
  1. ルート CLAUDE.md は「`<project>/CLAUDE.md` を都度読め」と規定するが、`thinkx/CLAUDE.md` に
     views ビルドの記載も `thinkx/docs/` への言及も無い。**規定どおり読んだ唯一の文書が
     必要な事実を持っていなかった。** これが主因。
  2. `docs/SITE_REQUIREMENTS.md` はルート CLAUDE.md のどこからも参照されていない。
  3. ルート CLAUDE.md L30 が `thinkx-system/SITE_EDIT_WORKFLOW.md` を指すが実体は
     `docs/SITE_EDIT_WORKFLOW.md`(他行は `docs/` 付き。ここだけ欠落)。ただし同文書は
     ビルド詳細を持たず「カットオーバー前は未発効」のため、今回の直接原因ではない。
  4. 同型の3サイト(thinkx / kazukiotsukacom / transformism)は package.json のビルド
     スクリプトが一字一句同じで、**3つとも CLAUDE.md にビルド記載が無い**。
     配線を直さない限り**どのサイトでも再発する**。
- **再発防止**: 編集前に `git check-ignore <path>` を打つ(ignore = 生成物を疑う)。
  文書側の配線(役割別必読の新設・3サイト CLAUDE.md へのビルド節・SITE_REQUIREMENTS への
  コマンド明記・受賞企業ページの作り方 §2-4 への babel 追記)は提案済み・オーナー承認待ち。

### F-E15(要判断): `GeosansLight` が指定されているのに読み込まれていない

- **実測(2026-07-21)**: ビルド済み `views/css/main.css` と本番 `truetechjapan.com/css/main.css`
  の双方で **`@font-face` が0件**。Typekit の kit(`bez6hty` / `qbw6sek`)はどちらも収録が
  `yu-gothic-pr6n` のみで `GeosansLight` を含まない。ローカルの `@font-face` は
  `src/less/main.less:23-29` でコメントアウトされている。**供給源がどこにも無い。**
- **指定箇所**: `src/less/top.less:162,519,528` / `apply_page.less:8` /
  `article_page.less:11` / `ir_page.less:8` の計6箇所。うち top.less の3箇所は
  thinkxinc.com トップに**実在・表示中**の要素に当たっている。

  | 箇所 | 実際のテキスト |
  |---|---|
  | `top.less:162` | `<div class="message">The fusion of science and art</div>` |
  | `top.less:519` | `<h2 class="title">Quantification of the Sixths Sense</h2>` |
  | `top.less:528` | `<h3 class="subtitle">The Fusion of Science and Art</h3>` |

  `apply_page` / `article_page` / `ir_page` は該当ページの現役性を未確認。なお top.less は
  `'GeosansLight', "yu-gothic-pr6n", sans-serif` とフォールバックを持つが、他3つは
  `font-family: "GeosansLight";` 単独で代替指定が無い。
- **含意**: **現在見えている見た目が既にフォールバック後の姿。** `@font-face` を復活させると
  今の見た目が変わるため、これはバグ修正ではなく設計判断。オーナー要件「指定したフォントが
  表示されていなければならない」には現状違反している。
- **判断の選択肢**: (a) 今の見た目が正なら CSS から `GeosansLight` の指定を消す(宣言と実態が
  一致する) (b) 本来当てたかったなら `@font-face` を復活させる。フォントファイルは
  `views/fonts/GeosansLight.ttf`(60,072 B)が本番で 200 を返す状態で生きている。
  復活させる場合、TTF のままより woff2 変換の方が軽い(要ライセンス確認)。

### F-E16(実測): トップページの動画資産

- **背景動画**(`index.html:48` / `autoplay muted loop` / `z-index:-1` の全面背景):
  `Sitetop2025_7.mp4` は 1920x1080・43.8秒・**9.96 Mbps**・54.4MB・音声トラック有り。
  HTML で `muted` 指定なのに音声を配っていた。装飾用途に対して5倍前後の過剰品質。
  → `Sitetop2025_7_13noaudio.mp4`(2.46 Mbps / 13.5MB / 音声無)へ差し替え(**−75%**)。
- **Learn More**(`index.html:55` / クリック時のみ): `VNMachineCloudIntro1.1.mp4` 148.0MB
  → `VNMachineCloudIntro1.1_21MB.mp4` 21.0MB(**−86%**)。尺・解像度は原本と一致。
- **不採用**: `Sitetop2025_7_com16.mp4` は `moov` アトムが末尾で faststart が効かず、
  16.7MB を全部落とすまで再生が始まらないため却下。**mp4 は配置前に moov 位置を確認すること。**
- **製品動画4本は無実だった**: `preload` 未指定時の既定は `auto` ではなく `metadata` で、
  `moov` は各 10KB 程度・4本合計で約350KB しか取らない。当初「78MB を先読みしている」と
  報告したのは誤りで、ファイルサイズからの決めつけだった。`preload="none"` は先頭フレームの
  表示と再生の即応性を失う交換になり、割に合わないため**適用しない**。
- **`views/video/` は本番へ運ぶ経路を持たない**: gitignore 対象(`thinkx/.gitignore:36`)かつ
  infra のデプロイスクリプトに `video` の記述が一つも無い。staging へは filedrop
  (`main.py:787` / hostname が `-stg` の時のみ)で入れられるが本番では 404 になる。
  CSS/JS はビルドで再生成できるため `31664de` の配線で解決したが、動画は生成できないため
  同じ手が使えない。→ `docs/TODO.md` #6。

### F-E17(実測): route_sweep ゴールデンの `/filedrop: 200` は staging ホスト依存

- イベントページ追加(2026-08-05)の検証でローカル Mac から `pytest tests/` を実行したところ、
  唯一の赤が `/filedrop`(golden 200 / actual 404)。filedrop はホスト名 `-stg` 判定
  (`855f736` の修正)なので、**staging 以外のマシンでは sweep がこの1件で必ず赤になる**。
  今回の変更(イベント2ルート追加)は golden 通りに 200 で緑。ゴールデンは触っていない。
- 対処の選択肢は (a) 現状維持(staging で回すのが正) (b) テスト側で hostname を
  スタブして環境非依存にする。規範化は人間の判断。

### F-E18(既存の穴): `AVAILABLE_LANGS` の ko/de に page_metadata が無く既存ページは /ko/* で 500

- `config.py:94` は 9言語(ko/de を含む)を許すが、`locales/page_metadata.json` の既存
  `metadata_*` エントリは 7言語のみ。`/ko/about` 等は language_wrapper を通過した後
  `metadata_*[lang]` の KeyError で 500 になる(既存挙動・全ページ共通)。
- 新設のイベントページ(`/event/deepsocietyclub3.html`)は独立ページ方針(オーナー指示
  2026-08-05)で locale・language_wrapper を使わないためこの穴の影響を受けない。
  既存ページの扱いは要判断。
