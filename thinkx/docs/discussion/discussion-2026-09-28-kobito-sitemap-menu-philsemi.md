2026-09-28 KOBITO の sitemap 追加・generator 廃止・製品メニュー追加・philsemi2609 準備中削除（生ログ）

引用（太字）がオーナーの発言で、原文のまま。続く地の文が Claude の応答（実際に返した内容。
冗長な部分のみ圧縮）。時系列。確定事項は thinkx/docs/DECISIONS.md（T-1/T-2）と
docs/GUIDELINES.md（2026-09-28 の項）が正。

> **thinkx KOBITOの製品ページをsitemapに追加して**

sitemap.xml は generate_sitemap.py が生成する構造だったため、generator に KOBITO を追加して再生成した。KOBITO は `/products/KOBITO`（言語プレフィックスなしの独立ルート）なので quantz 外部ページと同様の特殊ケースとして追加（priority 1.0）。コミット 15ed06f・push 済み。

staging 反映の途中で、develop へのマージスクリプトが「未 push コミット 2 件（podcast 切り抜きトラック）」を検出して停止。同じ作業コピーで並行して動いている podcast セッションに SendMessage で push 可否を確認し、返信があるまで push を保留した。

---

> **> generate_sitemap.py にKOBITOを追加してsitemap.xmlを再生成します。KOBITOは/products/KOBITOという言語プレフィックスなしの独立ルートなので、quantz外部ページと同様に特殊ケースとして扱う予定で、まずはsitemapがゴールデンテスト等で参照されていないか確認します。**
>
> **これは遠回りでは？本来pythonと別にページデータがあるべきだしそれはxmlが本質的に担うからgeneratorが要るの？**

指摘のとおり generator の存在価値自体が怪しい。現構造ではページ一覧が 3 箇所（main.py のルート定義・generator 内の pages リスト・生成物 sitemap.xml）に重複し、generator の仕事は言語展開（en/ja）と priority 整列だけ。エントリ 30 件弱・低頻度の規模では二重管理のドリフト危険が利得を上回る。

選択肢を 3 つ提示: A. generator 廃止・xml 直接編集（推奨）、B. 現状維持、C. main.py ルートから導出（priority 等の方針情報が要るためこの規模には過剰）。

---

> **A**

（同ターンで podcast セッションから「push 済み・staging に流して支障なし」の返信あり）

A 案を実行。generate_sitemap.py を削除し、sitemap.xml（KOBITO 入りの現生成結果）を唯一の正とした。決定を thinkx/docs/DECISIONS.md（新設）に T-1 として記録。

このとき事故が 1 件発生: 削除を `git rm` で stage した直後、並行の infra 記録セッションのコミット 84496f4 が stage 済みの削除を巻き込んでコミット・push した（同一作業コピー・同一 index を複数セッションが共有しているため）。ツリーの最終状態は意図どおりだが履歴の帰属が濁った。force push 禁止のため書き換えず、root findings.md に記録（対処案: worktree 隔離、またはパス指定コミットの規約化。規範化はオーナー判断）。以降このセッションのコミットは全てパス指定で行った。

---

> **ただしページが追加されたらsitemapの更新をオーナーに提案する（優先度は確認を仰ぐ）フローを定型化しろ**

docs/GUIDELINES.md に原文つきで記録し、thinkx/docs/DECISIONS.md に T-2 として登録。内容: サイトにページ（ルート）を追加・公開したら、その作業のうちに sitemap.xml への追記をオーナーに提案する。提案には URL と priority の案を添えるが、priority は実行者が決めずオーナーの確認を得てから書く。対象は thinkx の sitemap.xml / sitemap_NNTM.xml / sitemap_truetechjapan.xml など各サイトの sitemap 全て。

staging デプロイ実行（sitemap 追加+generator 廃止+podcast 2 件+infra 記録が同乗）。staging web 上で sitemap.xml 内の KOBITO エントリと `/products/KOBITO` の 200 を実測確認。本番反映用コマンド（deploy_production_from_develop.sh）を提示。

---

> **当社の製品メニューの一番下に KOBITOサーバークラウド　を追加しよう　KOBITO Server Cloud**

header.html と footer.html の両方にある製品リストの一番下（NNTM の下）に `/products/KOBITO` へのリンクを追加。ラベルは日英で異なるため、サイトの流儀どおり locale（locales/header.json）に `menu_content_kobito` として追加: ja「KOBITOサーバークラウド」/ en「KOBITO Server Cloud」。他言語（zh/es/ru/fr/ar）は他製品と同様に英語表記のまま（翻訳を勝手に作らない）。

ローカル（http://127.0.0.1:5000）で日英のヘッダードロップダウンとフッターを実測確認し、スクリーンショット 3 枚を送って OK を待った（見た目変更はローカル+スクショで OK をもらってから staging のルール）。コミット 30b33bb（パス指定）。

---

> **OK**

push → develop マージ → staging デプロイ。staging web 上で ja ページに `/products/KOBITO` リンク 2 箇所（header+footer）・ja/en ラベルを実測確認。全サイト疎通 200。podcast の C-1〜C-3 とリモコン関連コミットが同乗（他セッションが push 済み・追加系で衝突しない旨確認済み）。

---

> **https://thinkxinc.com/event/philsemi2609 の準備中２名分を消して**

philsemi2609.html の GUESTS セクション、ゲスト・パネラー欄のプレースホルダ 2 件（写真枠+氏名の「準備中」）を削除。これでしか使っていなかった placeholder 専用スタイル（CSS 変数 2 つ・.performer-photo-placeholder・.performer-name.preparing）も併せて除去。ローカルで「準備中」0 件・200・レイアウト崩れなしを確認し、スクリーンショット 2 枚を送って OK を待った。コミット 7baac9e。

削除箇所の Jinja コメントに「確定後に氏名（永井照明 / Jonathan Katz）へ戻す」のメモがあった点を報告（掲載時は 7baac9e の直前から枠を復元できる）。

---

> **OK**

push → develop マージ → staging デプロイ。staging web 上でページ 200・「準備中」0 件を実測確認。本番反映用コマンドを再提示（イベントページ修正・sitemap・メニュー・podcast/リモコン分がまとめて出る）。

---

> **OK このセッションは記録して閉じる**

本番の反映を実測確認: sitemap.xml に products/KOBITO 1 件、/ja/ にメニューリンク 2 箇所、philsemi2609 に「準備中」0 件（オーナーが本番デプロイを実行済み）。記録一式（本議事録・DECISIONS T-1/T-2・GUIDELINES・findings）を揃えてクローズ。

## 到達点

- sitemap は xml 直接編集が正（T-1・generator 廃止）。ページ追加時は sitemap 更新をオーナーに提案し priority は確認を仰ぐ（T-2・定型フロー）。
- KOBITO は sitemap・製品メニュー（header/footer・日英）の両方に掲載され、本番反映済み。
- philsemi2609 の「準備中」2 名分は削除され本番反映済み。復元は git 履歴（7baac9e 直前）から。
- 並行セッションとの index 共有によるコミット混入事故を root findings.md に記録。対処の規範化はオーナー判断待ち。
