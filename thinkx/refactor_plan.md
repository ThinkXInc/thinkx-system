# 静的サイト群 vendoring カットオーバー計画書 v1.1(S トラック)

対象: thinkx(truetechjapan アセット含む)+ kazukiotsukacom / 作成日: 2026-07-07(v1.1 同日改訂)
v1.1 の変更点: Phase 2 完遂を受けて S-0a の前提を具体値で確定(v2.0.0 実在・tree hash 実測値を記入)。
findings.md の置き場所を明記(各サイト自身のリポジトリ)。citywalk(C トラック)は本計画の対象外である
ことを明記。作業項目の構成に変更なし。
性質: **リファクタリングではない**。libcommon の消費形態を submodule → vendoring(v2.0.0)へ
切り替える構造変更のみ。サイトのコードは1行も変えない。
正本はこのファイル1箇所(thinkx/refactor_plan.md)。kazukiotsukacom 側に複製を置かない。

---

## 大原則

1. **両サイトは稼働中である。** quantz と異なり本番挙動が現に存在する。したがって
   オラクル(S-0b のスモーク)を建ててから触る。スモークのゴールデン不変が全項目の絶対条件。
2. **サイトコードは挙動保存どころか無変更。** 両サイトは libcommon の[凍結]面のみを消費する
   ことが実測で確定しており(libcommon 計画 §1.2)、[凍結]面の挙動同一性は libcommon 側の
   特性テスト(T-L1〜T-L6・ゴールデン不変)が既に機械証明している。本計画が検証するのは
   「配線の切り替え(submodule→実物コピー)がサイトの import と応答を変えないこと」だけである。
3. 1項目=1コミット+push。ブランチは `2026refactor`(D-14。両サイトで新規作成)。
   発見は **各サイト自身のリポジトリ直下の findings.md** へ(S-0b で新規作成。
   Security exception は即停止・D-22)。パスは明示(D-21)。
4. **citywalk(C トラック・Phase 4c)は本計画の対象外。** 本計画は thinkx +
   kazukiotsukacom の2リポジトリのみを触る。citywalk/refactor_plan.md は別トラックの
   規範であり、参照も流用もしない(1セッション=1計画書)。
5. **本番サーバへのデプロイは本計画の範囲外。** 計画はリポジトリ上のカットオーバーと
   ローカルスモークまで。デプロイのタイミングは人間が決める(ロールバックは直前コミット)。

## 前提(S-0a で機械確認)

- libcommon の Phase 2 が完遂している: タグ `v2.0.0` が存在し、`scripts/bake.sh` が存在し、
  全ゲート(pytest / ruff / pyright)green。
- **パラメータ(実測済み・着手時に再確認):** v2.0.0 の tree_sha256 =
  `3359309a30a392a75a97b3fad594569487cb07068f770877202de3096fb57cf0`
  (quantz-web Q-6 の VERSION より実測。S-0a で libcommon v2.0.0 タグから bake.sh の算出法
  (.pyc/__pycache__ 除外)により再算出し、この値と一致することを確認してから進む。
  不一致なら停止・報告 — bake.sh か本計画のどちらかが誤っている)。
- ワークスペース settings.json の変更(人間が S-0a 時点で適用):
  `"Edit(thinkx/**)", "Write(thinkx/**)", "Edit(kazukiotsukacom/**)", "Write(kazukiotsukacom/**)"`
  の deny 4行を削除し、代わりに次の4行を追加する(スコープ強制を「サイト全体」から
  「vendoring 先のみ」へ切り替える):
  `"Edit(thinkx/web-server/libcommon/**)", "Write(thinkx/web-server/libcommon/**)",
   "Edit(kazukiotsukacom/web-server/libcommon/**)", "Write(kazukiotsukacom/web-server/libcommon/**)"`

## 作業項目(実行順)

### S-0a 前提ゲート
- **完了条件:** `git -C libcommon tag -l v2.0.0` が非空(Phase 2 完遂済み・確認のみ)/
  `test -f libcommon/scripts/bake.sh` / 上記パラメータの再算出一致 /
  libcommon で pytest・ruff・pyright すべて exit 0 / settings.json の切り替えが人間により適用済み。
  いずれか不成立なら着手しない。
- **コミット:** なし。

### S-0b スモークハーネス(両サイト・これが稼働サイトのオラクル)
- **変更:** 各サイトに `tests/conftest.py` + `config_test.py`(main.py L16 の `check_config` が
  要求する REQUIRED_KEYS_IN_CONFIG を全て埋めたテスト用 Config。実値は不要、形式が通ればよい)。
  DB 等への import 時接続があれば quantz Q-1 と同型の差し込みを行う(両サイトの消費面からは
  不要の見込み。必要になった事実は findings に記録)。テストは2本:
  (a) `from main import app` が成功する、(b) `app.url_map` の全 GET ルートへ test client で
  アクセスし (ルール, ステータス) 表をゴールデン凍結(quantz Q-2 のミニ版)。
- **完了条件:** 両サイトで pytest exit 0、ゴールデンがコミット済み。
- **コミット(各サイト):** `test: smoke harness and route golden before vendoring cutover`

### S-1 thinkx カットオーバー
- **変更:** (1) `git submodule deinit -f web-server/libcommon` → `.gitmodules` から該当節を削除
  (**playbooks submodule には触れない**)、(2) `bash libcommon/scripts/bake.sh v2.0.0
  thinkx/web-server/` で焼き込み(VERSION 生成)、(3) VERSION の tree hash が S-0a の
  パラメータと一致することを確認(`.pyc`/`__pycache__` 除外後。bake.sh v1.8 仕様)。
- **完了条件:** clone 直後相当(submodule update なし)で S-0b スモークが green・
  **ルートゴールデン不変** / VERSION hash 一致 / `git status` に想定外の差分なし。
- **リスク/戻し方:** `git checkout -- . && git submodule update --init web-server/libcommon`
- **コミット:** `build: vendor libcommon v2.0.0, retire submodule`

### S-2 thinkx デプロイ経路の submodule 依存検査
- **変更:** deploy.sh・playbooks(submodule の中身を含む)・CI 設定から
  `git submodule update` / `--recurse-submodules` 相当の記述を grep で検査。
  **playbooks 内に該当があれば修正せず findings に記録して人間判断**(playbooks は別リポジトリ
  であり本計画の対象外。libcommon 分の submodule 取得だけが不要になる——playbooks 自体の
  submodule 取得は残す必要がある点に注意)。thinkx 直下のスクリプトに該当があれば、
  libcommon 分の行のみ削除。
- **完了条件:** 検査結果(該当箇所の一覧または0件)が findings に記録されている。
- **コミット:** 変更があった場合のみ `build: drop libcommon submodule step from deploy path`

### S-3 kazukiotsukacom カットオーバー(S-1 と同型)
- S-1 の (1)〜(3) を kazukiotsukacom に適用(こちらは submodule が libcommon の1つだけ)。
  デプロイ経路検査も同時に行う(S-2 と同じ規則)。
- **完了条件・戻し方・コミット:** S-1/S-2 と同一。

### S-4 各サイトの CLAUDE.md 新設(この内容の通りに)

```markdown
# <サイト名> 開発規約

- 本サイトは libcommon の[凍結]面(logger/color/validator/locale/language/
  レスポンスフォーマット族/mail 等)のみを消費する。flask_helpers / session は使わない。
- web-server/libcommon は vendoring された実物コピー(VERSION 参照)。**編集禁止**。
  修正は libcommon 原本で行い、bake.sh で焼き直す。
- 検証: pytest(スモーク+ルートゴールデン)。libcommon を焼き直したら必ず実行する。
- config.py + .env が設定の正。libcommon の各モジュールはホストの config を読む(現行仕様)。
```
- **完了条件:** 両サイトにファイル存在・内容一致。
- **コミット(各サイト):** `docs: add CLAUDE.md`

### S-5 最終検証
- 両サイトで pytest green(ゴールデン不変)/ VERSION hash 一致 / push 済み。
- ROADMAP の Phase 2.5 チェックは人間が更新。**本番デプロイは別途人間がスケジュール**
  (デプロイ後の確認はブラウザでのトップページ表示——これは人間の1分作業として許容する。
  稼働中サイトの最終確認だけは機械化より目視が安い)。

## やらないこと

| 禁止事項 | 理由 |
|---|---|
| サイトコードの変更・改善(thinkx 独自 flask_helper.py の統合=F-7 を含む) | 本計画は配線切り替えのみ。サイト改善は次期 |
| playbooks リポジトリの変更 | 対象外。該当があれば findings +人間判断 |
| libcommon スナップショットの編集 | D-10。settings deny で強制 |
| 本番デプロイの実行 | 人間がスケジュール(大原則4) |