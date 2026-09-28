# thinkx の決定事項(DECISIONS)

thinkx サイトに固有の確定済み決定を記録する。ワークスペース全体に関わる決定は
`thinkx-system/docs/DECISIONS.md` に書く。実行者(Claude Code)が追記できるのは
**オーナーが下した決定の記録**のみ。自分で決めた方針を決定として書かない。

| # | 決定 | 一行根拠 | 日付 |
|---|---|---|---|
| T-1 | sitemap.xml は手で直接編集する(正は xml の 1 箇所)。generate_sitemap.py は廃止 | ページ一覧が routes(main.py)・generator 内リスト・xml の 3 箇所に重複し、generator の仕事は言語展開と priority 整列だけ。30 件弱・低頻度の規模では二重管理のドリフト危険が利得を上回る | 2026-09-28 |
| T-2 | ページを追加したら sitemap.xml への追記を**オーナーに提案する**(priority は自分で決めず確認を仰ぐ)。定型フローの詳細は `docs/GUIDELINES.md`(root)2026-09-28 の項 | generator 廃止後は sitemap 更新が自動で伴わないため、ページ追加とセットの定型手順として固定する | 2026-09-28 |
