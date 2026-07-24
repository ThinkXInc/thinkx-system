# citywalk 進捗

更新日: 2026-07-23
現在フェーズ: C-0c UI知覚オラクル構築（未完了）

## ここまで完了

- C-0a/C-0b: legacy取り込み、秘密根絶、規範配置。
- ground truth動画をGit LFSで配置。
- ground truthの21アニメーション区間を確定。
- 高密度motion referenceを2,240枚抽出し、オーナー承認に基づきGit LFSで管理。
- fixtureによるJinja直レンダリングを廃止し、旧business blueprintを実ブラウザで起動。
- 旧ECMA 47ファイルをBabelで再現build。
- Redis依存は `fakeredis==1.7.1` で解決。
- 欠落した `session.js` / `main.js` は旧履歴上も実体がない無害なdead referenceとして許容。
- Google Mapsの実ロード、center、zoom、pointer状態をUI試験で検証。
- 層1静止画を `web-server/tests/golden/ui_legacy/static/` に12枚凍結。
- 誤ったsignin fixture goldenを削除。
- motion契約、rAF trace検証、Chrome CDP PNG screencastを実装。
- ground truthとlocal flowの対応表を作成。
- translation結果11件とdropdown操作を外部送信なしのtest-only fixtureで再現。
- local frameのChrome timestampからFFconcat時間表を作り、並列動画での誤った速度伸縮を排除。
- `freeze:legacy-motion` を、収録→trace検証→並列動画生成のfail-fast pipelineとして追加。
- ground truth、台帳、契約、層1画像のchecksum全24項目を検証済み。
- `git lfs fsck` green。

## オーナー確認

- 2026-07-23: 層1静止画12枚を承認済み。
- モバイル未対応によるSettings/Signup等の崩れも、旧UI保存基準として許容済み。
- アニメーションは未確認・未承認。
- 日本語の確認基準は `web-server/tests/golden/ui_legacy/OWNER_REVIEW_JA.md`。

## 現在greenの検証

- 旧blueprint server: 2 tests green。
- motion contract test: green。
- motion trace validator test: green。
- 実Chrome screencast smoke test: green。
- 旧ECMA Babel build: 47 files success。
- 層1実ブラウザUI oracle: 1 test green（オーナー端末で実Mapsキーを渡して確認済み）。

## 未完了

- `motion/` のlocal実収録成果物は未生成。
- `motion_trace.json` は未生成。
- ground truth対localの `review_*.mp4` 6本は未生成。
- 6本のアニメーションをオーナーが目視確認していない。
- motion成果物のchecksumと承認記録は未作成。
- したがってC-0c全体は未完了で、C-1へ進んではならない。

## 次回の開始点

1. Codexプロセスへ `CITYWALK_GOOGLE_MAPS_API_KEY` が安全に渡された状態で、citywalk直下から
   `npm run freeze:legacy-motion` を実行する。
2. `motion_trace.json` の自動検証がgreenであることを確認する。
3. `motion/review_*.mp4` 6本をオーナーへ提示する。TSVや英語READMEを読ませない。
4. オーナー承認後に、生成物のchecksumと承認日を `CHECKSUMS` と `findings.md` に記録する。
5. ここまで完了して初めてC-0c完了を判定する。C-1開始はその後。

## 守る条件

- `.env` やMapsキーの値を読み、表示し、成果物へ保存しない。
- `web-server/tests/.build/` は生成物なのでコミットしない。
- 地図タイルの絵柄は比較対象外。操作順、速度、軌跡、非地図UI、文言反映を比較する。
- §7-4未裁定のためC-3禁止。
- §7-3未裁定のためC-4g禁止。
- 単一directory・単一branch運用はD-49に従う。他トラックの未コミット変更に触れない。

## 主要コミット

- `a291201`: C-0a/C-0b legacy取り込み・秘密根絶・規範配置。
- `bce5d83`: C-0c ground truth区間・高密度frame抽出。
- `42a11bf`: 旧blueprint実起動と層1UI oracleを含む共有merge。
- `af08fcc`: legacy motion契約。
- `d4e45d3`: motion capture harness。
- `afa9000`: motion trace validator。
- `875ffff`: 層1goldenを `static/` へ配置。
- `9cf76e6`: C-0c入力checksum。
- `d822ebb`: Chrome screencast smoke test。
- `2ebbb44`: fail-fast motion freeze pipeline。
- `ada5093`: local motion timestampの保持。
- `d539e79`: 日本語オーナー確認票。
- `ae49a44`: 層1オーナー承認記録。
