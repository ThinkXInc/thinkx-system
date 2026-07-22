# TODO 台帳(横断・恒久)

作戦に紐づかない横断的・恒久的な課題を置く。着手条件が揃っていない、または
今すぐやるべきでないと判断したものを、判断ごと残すための表。

`docs/NEXT_CYCLE.md` との違い: あちらは 2026 リファクタリング作戦からの繰延で、
作戦完了とともに `docs/archive/monorepo_refactor_2026/` へ格納される。本表は
archive されない。作戦をまたいで残る課題はこちらに置く。

優先度: **高** = 実害が出ている / 放置で悪化する ・ **中** = 改善価値が明確 ・ **低** = 気づきの記録

| # | 項目 | 優先度 | 対象 | 状態 |
|---|---|---|---|---|
| 1 | Typekit の和文フォント 1.9MB 取得を軽くする | 高 | 全サイト共通 | **設定変更済・効果未実測** |
| 2 | libcommon が `AWS_ACCESS_KEY_ID` を平文でログ出力する | 高 | libcommon 原本 + vendored 全コピー | 未着手 |
| 3 | `base.html` の言語リダイレクトが `load` 依存 | 中 | thinkx 系サイト | 未着手 |
| 4 | transformism の表示開始が `load` 依存(thinkx と同一の地雷) | 高 | transformism | 未着手 |
| 5 | css/js に gzip が効いておらず Cache-Control も無い | 中 | loadbalancer | **修正済・nginx reload 待ち** |
| 6 | `views/video/` を本番へ運ぶ経路が存在しない | 高 | thinkx(構造) | 未着手 |
| 7 | `GeosansLight` が指定されているのに読み込まれていない | 中 | thinkx | オーナー判断待ち |

---

## 1. Typekit の和文フォント 1.9MB 取得を軽くする(優先度: 高)

- **原文**(オーナー 2026-07-21): 「これについては確かに問題であるが、全てのサイトに共通しているし、
  何かこのフォントを変えたいとは思っていない。もっと早くできる方法があるならそうしたいが。
  それは今すぐにやるべきことだとは考えていない。」「このTypekitの問題は割と優先度が高い。」
- **問題**: Typekit(kitId `bez6hty`)が `m?features=ALL&v=4&chunks=…` で **1,888 kB** を取得する。
  自前資産(document + CSS + JS + 画像)が約 160 kB なので、**ページ重量の約 93% が
  このフォント1本**。実測: staging `/ja/award/revorn`・2026-07-21・DevTools Network。
- **制約**: **書体は変えない。** フォントの差し替えは選択肢に入れない。

### 調査で判明したこと(2026-07-21・当初の推測は誤りだった)

Adobe Fonts の管理画面を実見して、当初立てた仮説が2つとも外れていたことが判明した。

| 当初の推測 | 実際 |
|---|---|
| 収録ウェイトを絞れば効く | **既に R/400/normal の1つだけ**。削る余地なし |
| 動的サブセットを有効化すべき | **既に Dynamic Subsetting 有効**。設定済み |
| — | 真因は **Vertical Features + OpenType Features が全有効**(`features=ALL`) |

`jp78` `jp90` `jp04` `trad` は旧字体・異体字の別グリフ群、`ruby` はルビ用、
`fwid/hwid/pwid/twid/qwid` は幅違いの複製。動的サブセットは「どの文字を送るか」を
絞るが、機能を全要求すると各文字が異体字ごと付いてくる。
CSS/LESS 全体に `font-feature-settings` / `font-variant` / `writing-mode` /
`text-orientation` が**1件も無い**ことを確認済みで、これらは一つも使われていない。

### 実施した変更(2026-07-21)

- `Vertical Features` OFF / `OpenType Features` OFF → `featureSettings: "NONE"`
- `FONT DISPLAY` を `auto` → **`swap`**
- kit を旧 `bez6hty` から `qbw6sek` へ差し替え(commit a1d819d)

`optional` は不採用。初回訪問で代替フォントのまま差し替えないため、オーナー要件
「指定したフォントが表示されていなければならない」に反する。

### 未確認(次にやること)

**削減幅を実測していない。** 1,888 kB からどこまで落ちたかはブラウザでしか測れない。
デプロイ後に DevTools(`Disable cache`)で `m?features=…` の Size を見る。
あわせて日本語の見た目を目視確認する(理論上は標準合字が効かなくなるだけ)。
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
- **実施済み(2026-07-21 / commit 72535b6)**: `loadbalancer/nginx.conf` に `gzip_types` +
  `gzip_proxied any` 等を追加。**反映には loadbalancer の nginx reload が必要で未実施**
  (承認が要る操作)。`Cache-Control` は入れていない — conf.d の複数ブロックが自前の
  `add_header Cache-Control` を持ち、http レベルに置くと nginx の継承規則により
  そのブロックでは黙って無効化されるため、ブロック単位で別途判断する。

## 6. `views/video/` を本番へ運ぶ経路が存在しない(優先度: 高)

- **問題**: 動画は `thinkx/.gitignore:36` の対象で git に乗らず、**infra のデプロイ
  スクリプトに `video` の記述が一つも無い**。staging へは filedrop(`main.py:787`・
  hostname が `-stg` の時のみ有効)で入れられるが、本番では 404 になるため使えない。
- **今の危険**: 圧縮版への差し替え(commit 6e2eda4)は HTML の参照だけが git に乗っている。
  **このまま本番デプロイすると、本番は存在しないファイルを指して背景動画が消える。**
- **CSS/JS との違い**: あちらはビルドで再生成できるため `31664de` の配線
  (`build_and_restart.sh` の babel + lessc)で解決したが、**動画は生成できない**ので
  同じ手が使えない。運搬そのものの仕組みが要る。
- **選択肢**: staging から prod へ scp / 本番にも受け取り口を用意 / 動画だけ別の配布経路
  (S3 等)。いずれも本番への操作を伴うためオーナー判断が要る。

## 7. `GeosansLight` が指定されているのに読み込まれていない(優先度: 中)

- **問題**: ビルド済み CSS・本番 CSS ともに `@font-face` が0件で、Typekit の kit にも
  収録が無く、ローカルの `@font-face` は `main.less:23-29` でコメントアウト。
  **供給源がどこにも無い**まま6箇所で指定されている。詳細は `thinkx/findings.md` F-E15。
- **オーナー要件との関係**: 「英文でも和文でも指定したフォントが表示されていなければ
  ならない」に**現状違反している**。ただし今見えている見た目が既にフォールバック後の姿
  なので、復活させると見た目が変わる。バグ修正ではなく**設計判断**。
- **判断待ち**: (a) 今の見た目が正なら CSS から指定を消す (b) 本来当てたかったなら
  `@font-face` を復活させる(`views/fonts/GeosansLight.ttf` は本番で 200 を返す)。

## 8. デプロイの戻し(rollback)が未検証(優先度: 保留・オーナー判断 2026-07-22)

- **内容**: `sync_from_origin.sh` / deploy 経路の戻し(前 release への復帰)は実装以来
  一度も発火していない。意図的に staging を壊して確認する検証が未実施。
- **裁定(2026-07-22)**: オーナー判断で「ロールバックはほとんどやる見込みがない」ため
  **当面 TODO 据え置き・優先せず**。DNS 本番切替を先に進める。
- **関連**: DNS 切替後の戻しは DNS レベル(Route53 A を 123.226.234.127 へ)で成立し
  (`infra/docs/DNS切替手順.md` §5)、オンプレは温存されるため、当面はそちらが実質の戻し口。
