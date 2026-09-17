2026-08-24 fabula / podcast の monorepo 取り込み依頼と工程案（生ログ）

引用（太字）が発案者の発言で、原文のまま。続く地の文が Claude の応答（実際に返した内容。
冗長な部分のみ圧縮）。時系列。確定事項は thinkx-system/docs/PODCAST_TRACK.md（D-52）が正。

> **https://github.com/ThinkXInc/fabula**  
> **https://github.com/ThinkXInc/podcast**  
>
> **これらにはサイトが含まれる**  
> **thinkx-systemのmonorepoに含めて**  
> **fabula -> fabula-method.com ? 予定**  
> **podcast -> IP直打ちでアクセス 例　https://325.323.233.3**  
>
> **するとして，どのような工程が必要になるか　まずはstagingで podcastの編集UI　が開ければいい fabulaはあとでいい　その手順をだしてくれ**

両リポジトリと既存インフラを調査して工程案を提示した。要点:

- podcast の編集UIは `web/` サブコンポーネント。uWSGI 用 app は未実装で、動くのは
  標準ライブラリのみの `preview_local.py`（ポート8010）。データ（data/<ID>/）は git 外
- nginx-web-root には podcast 用の include 行が既にコメントアウトで予約されていた
- podcast リポジトリ内の議事録（2026-08-07 ホスティング検討・D-030）で「既存 EC2 に載せる・
  thinkx-system 移管後に WSGI 化」が既に裁定済みと判明
- 工程案: Phase 0 裁定（取り込み元・フォルダ名・公開方式）→ Phase 1 取り込み →
  Phase 2 構造合わせ → Phase 3 staging 稼働 → Phase 4 本番 → Phase 5 fabula（保留）

（翌 8/25 の Phase 0 裁定へ続く → discussion_20260825_Phase0RulingsAndSyncDesign.md）
