# TODO 台帳(横断・恒久)

作戦に紐づかない横断的・恒久的な課題を置く。着手条件が揃っていない、または
今すぐやるべきでないと判断したものを、判断ごと残すための表。

`docs/NEXT_CYCLE.md` との違い: あちらは 2026 リファクタリング作戦からの繰延で、
作戦完了とともに `docs/archive/monorepo_refactor_2026/` へ格納される。本表は
archive されない。作戦をまたいで残る課題はこちらに置く。

優先度: **高** = 実害が出ている / 放置で悪化する ・ **中** = 改善価値が明確 ・ **低** = 気づきの記録

| # | 項目 | 優先度 | 対象 | 状態 |
|---|---|---|---|---|
| 1 | Typekit の和文フォント 1.9MB 取得を軽くする | 高 | 全サイト共通 | 未着手 |
| 2 | libcommon が `AWS_ACCESS_KEY_ID` を平文でログ出力する | 高 | libcommon 原本 + vendored 全コピー | 未着手 |
| 3 | `base.html` の言語リダイレクトが `load` 依存 | 中 | thinkx 系サイト | 未着手 |
| 4 | transformism の表示開始が `load` 依存(thinkx と同一の地雷) | 高 | transformism | 未着手 |
| 5 | css/js に gzip が効いておらず Cache-Control も無い | 中 | loadbalancer | 未着手 |

---

## 1. Typekit の和文フォント 1.9MB 取得を軽くする(優先度: 高)

- **原文**(オーナー 2026-07-21): 「これについては確かに問題であるが、全てのサイトに共通しているし、
  何かこのフォントを変えたいとは思っていない。もっと早くできる方法があるならそうしたいが。
  それは今すぐにやるべきことだとは考えていない。」「このTypekitの問題は割と優先度が高い。」
- **問題**: Typekit(kitId `bez6hty`)が `m?features=ALL&v=4&chunks=…` で **1,888 kB** を取得する。
  自前資産(document + CSS + JS + 画像)が約 160 kB なので、**ページ重量の約 93% が
  このフォント1本**。実測: staging `/ja/award/revorn`・2026-07-21・DevTools Network。
- **制約**: **書体は変えない。** 手段は subset 化・ウェイト削減・読み込み方(`font-display`・
  preload・self-host)に限る。フォントの差し替えは選択肢に入れない。
- **背景と、問題の質が変わったこと(2026-07-21 追記)**: 表示が `window.load` 待ちだった頃は
  これが直接「表示まで6秒」を作っていた。表示開始を `DOMContentLoaded` に移した
  (`views/src/js/main.js`)ことで描画はもう待たないが、**代わりにフォントの差し替えが
  ユーザーに見えるようになった**(FOUT)。修正前は白画面の裏でフォント読み込みが隠れていた。
  オーナーが staging.thinkxinc.com で「フォントが正しく当たっていない気がする / 少し待ったら
  適用された」と観測したのがこれ。**壊れてはいないが、軽くすれば差し替えは知覚できなくなる。**
  よって「転送量が重い」ではなく「見た目のちらつき」として優先度が高い。
- **対象**: `templates/{truetechjapan,general,NNTM}/base.html` の3系統が同じローダ・同じ
  kitId(`bez6hty`)を持つ。使用フォントは `GeosansLight` と `yu-gothic-pr6n`(和文=重い方)。

## 2. libcommon が `AWS_ACCESS_KEY_ID` を平文でログ出力する(優先度: 高)

- **原文**(オーナー 2026-07-21): 「この問題は別のプロジェクトで解決したはずだった。つまり、
  libcommonの最新版ではこの問題は消えているはずだった。だから、libcommonのバージョンを
  アップすれば、おそらく問題は消える。」
- **問題**: `libcommon/mail.py:48` がメールクライアント初期化時にアクセスキー ID を info ログへ出す。

  ```python
  logger.info(f'Mail client initialize with\nAWS_ACCESS_KEY_ID:{aws_access_key_id} SES_REGION:{region_name}')
  ```

- **前提が成立しないことを確認済み(2026-07-21 実測)**: 「最新版では消えているはず」は**成り立たない**。
  原本 `/src/libcommon` の HEAD(`a316494` = ARCHIVE.md の参照 SHA)にも同じ行が残っており、
  `git log --all -S` でこの文字列を触ったコミットは追加時の `0596dad fix mail` 1件のみ、
  **削除コミットはどの ref にも存在しない**。vendored コピーも thinkx / auth / transformism /
  kazukiotsukacom の**4本すべてに残存**。つまり**どこにも修正は無く、バージョンを上げても消えない**。
  「別プロジェクトで解決した」記憶の出所は未特定。
- **手当て**: B案(`docs/COMMON_LIB_POLICY.md`)に従い vendored コピーを直接修正し、原本と
  他サービスへ展開する。キー ID は秘密鍵ではないが、ログに残す設計を避ける。
- **注意**: 5 箇所すべてを直す必要がある。1 箇所だけ直すと**今回と同じ「直したはずが残っている」が再発する**。

## 3. `base.html` の言語リダイレクトが `load` 依存(優先度: 中)

- **問題**: `base.html`(`<head>` 内)の言語判定が `window.addEventListener('load', …)` で走る。
  先頭パスセグメントが言語コードでない URL に来た訪問者は、GTM / フォント等の完了を待ってから
  リダイレクトされる。
- **影響範囲**: `/ja/...` 付き URL は発火しないので**今回計測した6秒とは無関係**。効くのは
  プレフィックス無しの入口 — とりわけ **`truetechjapan.com/` に来た日本語話者**
  (`detectLanguage()` が `ja` を返し `defaultLang` の `en` と異なるため `/ja/` へ飛ぶ)。
  サイトの最も太い入口がこれに当たる。
- **手当ての方向**: 判定は `navigator.language` と `location.pathname` しか見ておらず DOM に
  依存しない。スクリプトは `<head>` 内にあるので、**イベント待ちを外して同期実行**すれば
  描画前にリダイレクトでき、表示のちらつきも同時に消える。リダイレクトループには注意。

## 4. transformism の表示開始が `load` 依存(優先度: 高)

- **問題**: `transformism/web-server/views/src/js/main.js` が thinkx と**同一の構造**を持つ。
  `initializeLayout()`(L141)内で `f.showSite()` → `document.body.classList.add('show')` を
  呼び、それを `window.addEventListener('load', …)`(L222)から叩いている。
  CSS も `body { opacity: 0 }` / `body.show { opacity: 1 }` で同じ。
  **thinkx で6000msを作っていたのと同じ地雷がそのまま生きている。**
- **全サイト調査の結果(2026-07-21)**:

  | サイト | 配信元 | `.show` のトリガ | 状態 |
  |---|---|---|---|
  | truetechjapan.com / thinkxinc.com / NNTM | thinkx(同一 main.js) | DOMContentLoaded | 修正済 |
  | kazukiotsuka.com | kazukiotsukacom | `setting.js:35` の `$(document).ready` | 元から正しい |
  | transformism.art | transformism | `main.js:222` の `window.load` | **未修正** |

  kazukiotsukacom の `views/src/js/main.js` は全体が `/* not used */` でコメントアウトされて
  おり、`.show` は `setting.js` が付けている。紛らわしいので調査時は注意。
- **手当て**: thinkx と同じ形(`DOMContentLoaded` + 二重 `requestAnimationFrame`)にする。
  ただし transformism の `load` ハンドラは `layoutHeader` / `initializeModal` も呼んでおり、
  そちらが実寸(画像読み込み後のレイアウト)に依存していないかを確認してから移す。
  **thinkx のように showSite だけを切り出す必要がある。**

## 5. css/js に gzip が効いておらず Cache-Control も無い(優先度: 中)

- **問題**: `https://truetechjapan.com/css/main.css` の応答に `Content-Encoding` も
  `Cache-Control` も無く、**117 kB が無圧縮で毎回飛んでいる**(実測 2026-07-21)。
  gzip をかければ **129,944 B → 18,157 B(86% 削減)**。
- **原因**: `loadbalancer/nginx.conf:79` に `gzip on;` はあるが、`gzip_types` と
  `gzip_proxied` が無い。nginx の既定は `gzip_types text/html` のみ・`gzip_proxied off`
  (プロキシ応答は圧縮しない)なので、CSS/JS には効かない。
- **既存の対応との関係**: `c180008 fix(nginx): css/js を gzip し、Cache-Control を明示する`
  は **`nginx-web-root/nginx.conf` のみ**を変更しており、truetechjapan 等を配る経路
  (loadbalancer → thinkx の nginx)には入っていない。同じ手当てを横展開する必要がある。

## 6. デプロイの戻し(rollback)が未検証(優先度: 保留・オーナー判断 2026-07-22)

- **内容**: `sync_from_origin.sh` / deploy 経路の戻し(前 release への復帰)は実装以来
  一度も発火していない。意図的に staging を壊して確認する検証が未実施。
- **裁定(2026-07-22)**: オーナー判断で「ロールバックはほとんどやる見込みがない」ため
  **当面 TODO 据え置き・優先せず**。DNS 本番切替を先に進める。
- **関連**: DNS 切替後の戻しは DNS レベル(Route53 A を 123.226.234.127 へ)で成立し
  (`infra/docs/DNS切替手順.md` §5)、オンプレは温存されるため、当面はそちらが実質の戻し口。
