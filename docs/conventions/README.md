# conventions — コーディング規約の原本(本フェーズでは非規範)

ここには ThinkX のコーディング規約・設計思想の原本を保存する(人間が配置):
- thinkx-coding-style.md … 「ThinkXでのコードの書き方」(音声書き起こし原本)
- coding-guide-2022.md   … Coding Guide wiki(2022, 公理: Minimalism/Uniqueness/Speed)

**実行者(Claude Code)への注意:**
- リファクタリング実行フェーズでは、これらは**非規範**である。原本は現コードと
  部分的に矛盾する(例:「クラス継承は基本行わない」と simplicity の継承階層、
  gulp 前提のビルド記述と現行ビルド)。矛盾した規約に従ってはならない。
- 各リポジトリの規範は、計画書が生成する CLAUDE.md(simplicity R-11 / libcommon L-7)。
- これらの原本を正規化(誤変換除去・quantz-web 反映・公理→契約→リポ→skills への
  層分解)する作業は Phase 3(auth 実装)の前提として ROADMAP に定義されている。
  その作業までは、新規コードの様式判断は「リポジトリ内の一貫した実例」を手本とする。