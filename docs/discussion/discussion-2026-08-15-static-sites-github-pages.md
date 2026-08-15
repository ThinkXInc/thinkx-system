# 2026-08-15 static-sites: GitHub Pages 即時公開の仕組みづくり(生ログ)

引用(太字)が発案者の発言で、原文のまま。続く地の文が Claude の応答(実際に返した内容。
冗長な部分のみ圧縮)。時系列(セッションは 2026-08-13〜15)。運用の正本は
`docs/GUIDELINES.md`「static-sites は『置いて公開してでURL発行』の即時公開置き場」の節。

> **static-sites にhtmlを置いた**
>
> **② GitHub Pages（無料・恒久・自分で更新したい人向け）**
> **GitHubにリポジトリを作り、index.html として置いて Settings → Pages を有効化。https://ユーザー名.github.io/リポジトリ名/ で公開されます。**
>
> **この手順で公開したいので手順をだして**

状態を確認した——対象は `static-sites/小学生単語_コピー用_1.html` の1ファイル、gh CLI は
kazukiotsuka でログイン済み(repo スコープ・ssh)なのでブラウザ操作なしで完了できる。
無料プランの Pages はリポジトリ public 必須である点、thinkx のデプロイ経路とは無関係の
独立リポジトリである点を明示したうえで、(1) `index.html` に改名して public リポジトリ
`static-sites` を作成し push、(2) `gh api .../pages -X POST` で Pages 有効化、(3) curl で
公開実測、の3ブロックを提示した。

---

> **まずまず、このサイトのスタティックサイズのフォルダの中には、これから複数のHTMLページを置いて、それを速やかに公開したい場合に、このリポジトリをつかう　したがって、インデックスHTMLというのは特に必要がないので、そのまま置いたHTMLファイルの名前のまま公開していい　なるべく人間の手続きを簡素化したい。ただ単にこのフォルダの中にHTMLを置けば、そして公開してと言ったら、もうURLを発行して公開というような流れにしたい　そのような手続きを準備するための手順をくれ。**

前回のブロックは未実行(リポジトリ未作成)だったので、複数HTML・ファイル名そのまま公開の
前提で組み直した。index.html への改名は廃止。

- `static-sites/publish.sh` を作成(変更系・bash.md 規約準拠)。1本で「フォルダ内の全変更を
  commit → main へ push → 各 HTML の公開 URL(日本語ファイル名は URL エンコード)を表示」まで行う
- `.gitignore`(.DS_Store)を作成
- 運用を `docs/GUIDELINES.md` に原文つきで記録、メモリにも保存
- 残る人間の手続きは初回セットアップ1回だけ(git init → gh repo create --public → Pages 有効化 →
  publish.sh)としてブロックを提示。以後は「HTMLを置く →『公開して』と言う → 実行者が
  publish.sh を叩いて URL を報告」の3手

---

> **Changes to be committed:**
> **  (use "git rm --cached <file>..." to unstage)**
> **    new file:   .gitignore**
> **    new file:   publish.sh**
> **    new file:   "\345\260\217\345\255\246\347\224\237\345\215\230\350\252\236_\343\202\263\343\203\224\343\203\274\347\224\250_1.html"**
>
> **K00TSUKA@MacBook-Pro-5 static-sites % git**
> **commit -m"init publish"**
> **[main (root-commit) b723107] init publish**
> ** 3 files changed, 94 insertions(+)**
> **K00TSUKA@MacBook-Pro-5 static-sites %   gh repo create static-sites --public --source . --push**
> **✓ Created repository kazukiotsuka/static-sites on github.com**
> **  https://github.com/kazukiotsuka/static-sites**
> **X Unable to add remote "origin"**

調査結果——リポジトリ作成(`kazukiotsuka/static-sites`)は成功、失敗したのは remote 追加のみ。
原因はローカルの `origin` が既に `git@github.com:ThinkXInc/static-sites.git` を指していたため
(GitHub 上に `ThinkXInc/static-sites` が 2026-08-13 作成・空・ADMIN 権限で存在していた)。
コミット b723107 はローカルに無事。記録類が kazukiotsuka 前提だったため kazukiotsuka 側で
続行する修正ブロック(origin 付け替え → push → Pages 有効化)を提示しつつ、org 側
(`thinkxinc.github.io`)で公開したい意図があるかを確認した。

---

> **ThinkXInc にしろよ**

ThinkXInc 側に統一した。origin は既に ThinkXInc を指しているので付け替え不要。
publish.sh の URL・GUIDELINES.md・メモリを `thinkxinc.github.io` 前提に更新(org 側を使う=
オーナー裁定 2026-08-15)。push → `gh api repos/ThinkXInc/static-sites/pages -X POST` →
publish.sh のブロックを提示。不要になった空の `kazukiotsuka/static-sites` は Web の
Danger Zone から削除可(現 gh トークンに delete 権限なし)と案内した。

---

> **ファイル名変えた**

セットアップ完了(Pages status=built)とファイル改名(`小学生単語_Group1.html`)を確認し、
publish.sh を実行。rename が commit 694da42 として push され、curl で `HTTP/2 200` を実測。
公開 URL は https://thinkxinc.github.io/static-sites/小学生単語_Group1.html
(エンコード形: `.../%E5%B0%8F%E5%AD%A6%E7%94%9F%E5%8D%98%E8%AA%9E_Group1.html`)。
旧ファイル名の URL は以後 404。

---

> **ここまでセッションを閉じるので記録して。**

本書を作成。到達した状態: `static-sites/` は独立 git リポジトリで origin =
`ThinkXInc/static-sites`(public・Pages 有効・main ルート配信)。以後の運用は
「`static-sites/` に HTML を置く →『公開して』→ `bash static-sites/publish.sh`(commit・push・
URL 表示)→ URL 報告」。index.html は使わず、置いたファイル名のまま
`https://thinkxinc.github.io/static-sites/<ファイル名>` で公開される。
