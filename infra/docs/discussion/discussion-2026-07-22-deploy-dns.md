2026-07-22 デプロイ経路の整合と DNS 本番切替（生ログ）

引用（太字）がオーナーの発言で、原文のまま（音声入力の誤字・口語もそのまま）。続く地の文が
Claude の応答（実際に返した内容。冗長な部分のみ圧縮）。時系列。確定事項の正本は
`infra/docs/DECISIONS.md`（D-68）、`infra/docs/GUIDELINES.md`、`infra/findings.md`、
`infra/docs/デプロイ手順書.md`。この文書は「なぜその結論に至ったか」の経緯を残すもの。

---

## 1. 積み残しの確認と方針

> **デプロイに関する作業をもう一度、最後どこまで行って何か積み残しがあったかをチェックしてくれ。**

引き継ぎ（`引き継ぎ_2026-07-21_デプロイ経路整理.md`）と git を突き合わせて報告。到達点は
「3回目の本番デプロイまで完走・アセット配布をデプロイに組込み済み」。積み残しは①手元を develop に
揃える（未実行）②rollback 未検証（最重要・未検証）③skip 通知文の主語、ほか未解決（同期途中死の穴・
ファイル名ハッシュ・確認対象の手並べ・transformism/kazuki 本番投入・DNS 本番切替）。

> **まず1番はやるだろう。2番はロールバックはほとんどやる見込みがないから、とりあえずまだTODOに入れといて、DNSを完全に切り替えようと思う。**

1番を実行しようとしたが、共有チェックアウトに別トラック（auth / citywalk）の未コミット変更があり
`merge_develop_into.sh` は clean tree を要求するため停止。取り込むべきは develop 側の 1 コミットのみ。
rollback は `docs/TODO.md` §8 に据え置きで記録。DNS は独立なので保留の影響なし。

---

## 2. dirty tree で戻せない — 手順の穴と手順書の書き方

> **（merge_develop_into.sh の FAIL 出力を貼付）こういう場合はどうするんだ。下の1の手順をまずやってから0をやればいいのか？**
>
> **0 staging -> local (monorepo branch) / 1 local (monorepo branch) -> PR -> develop / 2 develop -> staging / 3 staging -> production**
>
> **こういう風に書いたので、デプロイ手順書があったら同じように書いておいて。私の書き方はシンプルで、一瞬でわかるようにしてある。**

「1を先に」では直らない。FAIL の原因は順番でなく作業ツリーに未コミット変更が残っていること自体。
1（pr_and_merge）を打っても未コミットの citywalk はツリーに残り 0 はまた止まる。一般解は「区切りなら
commit してから、途中なら stash 退避 → 実行 → 戻す」。現行 `デプロイ手順書.md` は生の gh コマンドと
廃止済み `deploy.sh` を参照して古かったので、0-1-2-3 の簡潔形式に書き直した。

---

## 3. Evernote の deploy コマンド更新

> **（Evernote の実行コマンド一覧を貼付）これが私の手元にある Evernote の、私が実行するコマンドの一覧である。足りないものについてそのまま書き込めばいいような形で出してくれ。デプロイに関して、遠隔またはローカルで編集した時に、そこから先の手順を今のところこのチャットでいちいち出してもらうということに頼っているので、そうじゃないように自分の手元にリスト化しておきたいんだ。**

Evernote の「Deploy」節が現行と食い違っていた。①`deploy.sh prod/staging` は廃止（4本に分割）
②`infra/etc/push_assets.sh` は `infra/scripts/push_assets.sh` へ移動し、デプロイが自動で呼ぶので手打ち
不要 ③末尾「Transfer Video」の手動 tar 展開も不要。貼り替え用のファイルを渡した。

---

## 4. push_assets の向き

> **（push_assets のコマンドを貼付）これが行っているのはよくわからないんだが、ステージングからプロダクションに移しているのか。スーパーコムウェブワンというのはステージングがついていないからプロダクションのことだろう。プロダクションに移すということなのか、それともローカルからどこかに移すということなのか。どこからどこにということが全然わからない。**

`push_assets.sh <箱> <サイト>` は「ローカル Mac → 第1引数の箱」。送るのは git 管理外の
`views/video/`。`supercom-web1` は `-stg` なしなので本番 web。staging→prod ではない。手順書の
assets 節を「(local .../video/ -> prod .../video/)」と実パスで向きを書く形に直した。

---

## 5. citywalk の WIP を merge が巻き込んだ — 「このまま維持」

`merge_develop_into.sh` は clean を要求するが、develop の取り込みは citywalk のファイルには触れない
（触るのは docs のみ）ため、生の `git merge origin/develop` は dirty でも通ると判断して実行。ところが
マージ commit（42a11bf）が、並行 citywalk セッションが `git add` 済みだった WIP 18 件を丸ごと拾って
コミットしてしまった。未 push・作業は無傷である旨を報告し、どう処理するか確認。

> **（選択肢のうち）このまま維持**

42a11bf を維持。push は保留（citywalk の途中作業が伝播するため）と述べた。

---

## 6. 共有モノレポで乗るのは前提 / 摩擦は merge だけ

> **というか、他のセッションが、他のその他のセッションの変更を影響を受けるというか、結局セッションは1本のモノレポを共有しているんだから、他のセッションの変更が乗っかってくるのは最初から予定されていたことじゃないのか。**

その通り。乗ってくること自体は前提で事故ではない。引っかかったのは「乗ったのが未確定（未コミット）の
WIP で、そのコミット境界を私が勝手に決めた」点だけ。差し支えなければ問題なく、「維持」は妥当。

> **というか、つまり他のセッションが編集途中だとコミットができないということか。そんなことはないだろう。自分の作業範囲だけをコミットしてプッシュすることになるだろう。**
>
> **問題が起きるのは、ステージングから取ってくる時に編集中のファイルがあると取ってこれないということだろうか。だとしたら、どうするのがベストプラクティスだろう。**

正確。普通のコミットは各自が自分のパスだけ commit（`git add -A` を使わない）すれば無干渉。摩擦点は
develop の取り込み（merge）だけ。merge は「ツリー全体」を固める操作なのでパス指定ができず、並行
`git add` を巻き込む。ベストプラクティス＝共有ツリーで merge commit を作らない：(a) 自分のパスだけ
commit (b) develop→monorepo はリモートで PR merge (c) ローカルは `git fetch && git merge --ff-only`
でポインタを進めるだけ（ff は commit を作らないので他の WIP に触れない）。

---

## 7. 手順として決める — リモート PR + ローカル ff（D-68）

> **とにかくこういう状況は起こりうる。つまり、ステージングは編集されている。そして、他のセッションが編集中である。こういう状況にどうするべきなのかを手順として決めておかなければいけない。**

D-58（worktree 分離）は D-60 で撤回済み＝単一ディレクトリ・単一 branch が確定路線。topology 上
monorepo（auth 等の独自コミット）と develop（staging 編集）は分岐しているので実体の merge は必ず要る。
問題はそれを共有ローカルツリーでやること。決定：実体の merge はリモート（GitHub PR develop→monorepo）、
ローカルは `git merge --ff-only origin/monorepo` で追従。DECISIONS に D-68 として記録。

---

## 8. 対照スクリプトの新設と改名

> **ローカルでマージをするのをやめるのは、おそらくそれは正しいだろう。つまり、デベロップからモノレポへの PR を発行するということだろう。**
>
> **bash infra/scripts/pr_and_merge_to_develop.sh monorepo**
>
> **結局このスクリプトと対照的なものを作ればいいんじゃないのか。**

`pr_and_merge_to_develop.sh`（monorepo→develop）の対照として `pr_and_merge_to_monorepo.sh` を新設
（develop→monorepo の PR+merge をリモートで、末尾に手元を ff で追従する `ff_follow`。引数なし）。
旧 `merge_develop_into.sh`（ローカル merge）は廃止。参照（手順書・forward の戻し案内・DECISIONS・findings）
も追随。

> **pr_and_merge_to_monorepo.sh pr_develop_and_merge_to_monorepo.sh にしよう**

source（develop）を名前に明示するため `pr_develop_and_merge_to_monorepo.sh` に改名。内部の関数名・
使い方・全参照も追随。

---

## 9. Evernote を矢印形式に / 4本ライン通し実行

> **（Deploy 0-1-2-3 と Push assets の Evernote を貼付）こういう書き方だよ。**

矢印で「src -> [PR ->] dst (remote/local)」と向きを一目で示す形。手順書のステップラベルを矢印形式に
統一し、assets も実パスで向きを明記。GUIDELINES に「手順のステップは矢印ラベル」を記録。

> **（0-1-2-3 の通し実行ログを貼付）全部実行した。この4本のラインを打てば、デプロイが完了するとしたらかなりシンプルになったので、これでいいんじゃないだろうか。**

4本で完結、が正解。実際 0→1→2→3 が一気通貫で通り本番デプロイまで完走（release/2026-07-22 凍結、
thinkx 再コンパイル・再起動、本番4サイト 200、公開 DNS は未切替）。補足2点：step 0 の script 名が
`pr_develop_and_merge_to_monorepo.sh` に変わった（Evernote 差し替えを）／今回また実デプロイが完走した
ので DNS 切替の前提（正しいデプロイ確認後）が満たされた。

---

## 10. DNS 本番切替

> **DNSを切り替える。**

`DNS切替手順.md` の順で、step1 事前チェック（push_assets / check_request_path / acceptance-sweep /
証明書期限）を全 green 確認 → Route53 で apex A を 52.197.179.70 に手動変更 → 浸透確認 → 応答確認、を
paste-ready で提示。まず step1 を打って結果を、と依頼。

> **（step1 の出力を貼付。acceptance-sweep で `NG expect=200 got=404 /filedrop`、他は全 green）**

唯一の NG は `/filedrop`＝staging 専用機能（main.py:787：hostname が -stg のときだけ有効）。本番は
設計どおり 404 で、golden が staging 専用ルートを 200 期待に含んでいるだけ。他は全 green・https
end-to-end 200（＝LB の TLS が3ドメインとも有効）。finding に記録。

> **（証明書期限の出力を貼付。thinkxinc / transformism / kazukiotsuka とも notAfter=Sep 15 2026）**

3ドメインとも Sep 15 2026 まで有効（約55日・certbot 自動更新）。step1 完了・準備 OK として Route53 の
切替を依頼。

---

## 11. 確認対象の漏れ → server_name 自動生成の宿題

> **全部エレコードを差し替えた。 nntmapp.com truetechjapan.com もある これらもチェックスクリプトやチェックから盛れてないか**

指摘どおり。LB の server_name（配信ドメインの真実）から起こすと、私の3件リストと acceptance-sweep は
**truetechjapan.com・nntmapp.com・jessicas.online・nntm.thinkxinc.com・quantz.thinkxinc.com** を
落としていた。「手で並べると漏れる」の再発。全ドメインの dig+curl を提示。根治方針＝確認対象を
server_name から自動生成（finding に記録）。

---

## 12. 切替完了の確認（quantz 500・www 据え置き）

> **DNSを切り替えて、ちゃんと切り替わってるよ。**

全ドメインを実地確認。apex 5（thinkxinc / truetechjapan / nntmapp / transformism / kazukiotsuka）は
AWS・200。ただし www.* は A レコードそのものが無く解決不可、nntm./quantz. はまだオンプレ
（123.226.234.127）と判明し報告。

> **まだオンプレっていうやつは全部差し替えた。WWWは必要なんだろうか。必要ならやるが、あまり必要性を感じていない。**

再確認：nntm も AWS・200 に。quantz は AWS だが **500**——ただし切替前もオンプレで 500（回帰ではない）。
原因は AWS 本番に uwsgi が3つ（thinkx/kazuki/transformism）しか無く quantz app 未搭載なのに LB が
quantz.thinkxinc.com を流しているため。別トラック判断（載せる/畳む/放置）。www は「今は要らない」に
同意（apex 専用で索引がきれい・必要時に A 追加＋www→apex 301 で対応）。finding に記録。

---

## 13. filedrop 偽NG の除外 → exclude のリスト化

> **- filedrop の偽NG(本番向け golden から除外)**
>
> **これだけやって終わろう。**

正確な原因：acceptance-sweep は Host を常に公開名で当てるが filedrop は -stg 時のみ有効なので env に
関係なく sweep では常に 404。golden（サイト単体テストが正）は触らず、infra の sweep 側で
`thinkx:/filedrop` を対象外にし skip 行を出す形にした。実測：thinkx 58/58・ACCEPTANCE 全 green。

> **（対象外の case ブロックを貼付）これ一個一個個別に書くんじゃなくて、リストを作ってそのリストに含まれているものだったら対象外っていうふうにした方がいいんじゃないのか。**

> **それともそうなってんのか?そうなってんのか? このinの後にたくさんリストにできるんだったらいいよ。**

case を1件ずつでなく `exclude` 配列に集約し、既存イディオム `case " ${exclude[*]} " in *" $site:$path "*`
で所属判定。増えるときは配列に1行足すだけ。GUIDELINES に「繰り返す判定はリストに集約」を記録。

---

## 14. 記録

> **記録をつけることがあれば記録しといてくださいなければステーションを切る**

未記録のオーナー指示2件（判定のリスト化／手順の矢印ラベル）を GUIDELINES に追記。主要記録（DECISIONS
D-68・findings 各件・TODO §8）は反映・push 済みと報告。

---

## 到達点

このセッションで、デプロイは **0-1-2-3 の4本ライン**に確定した（0 staging→monorepo は
`pr_develop_and_merge_to_monorepo.sh`、1 monorepo→develop、2 deploy_staging、3
deploy_production_from_staging）。核心の設計判断は D-68：**共有ローカルツリーで merge commit を作らない**
——develop→monorepo の実体 merge はリモート PR で行い、ローカルは ff で追従して他セッションの編集中を
巻き込まない。これは共有チェックアウトで citywalk の WIP をローカル merge が巻き込んだ事故（42a11bf、
維持・push 済み）から得た教訓であり、D-60（worktree 撤回・単一 branch）と両立する形にまとめた。

DNS 本番切替は完了。apex 5ドメイン＋nntm がオンプレ（123.226.234.127）から AWS LB（52.197.179.70）へ
移り、すべて 200。残件は quantz.thinkxinc.com の 500（AWS 未搭載・別トラック判断）、www.* の据え置き、
rollback 未検証（TODO §8）、そして再発した「確認対象を手で並べると漏れる」の根治＝acceptance-sweep /
DNS 確認を LB の server_name から自動生成すること。filedrop 偽NG は sweep 側の exclude リストで解消した。

※このセッションに紛れた別セッション宛の投入2件（truetechjapan の「起業ページ」bot 可読化・supercom2
移行レポート v3）は「セッション違い」で取り下げたため、本記録には含めない。
