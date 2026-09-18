# 2026-09-18 本番504障害の復旧・assets除外・デプロイスクリプト改名・health check（生ログ）

引用（太字）がオーナーの発言で、原文のまま。続く地の文が Claude の応答（実際に返した内容。
冗長な部分のみ圧縮）。時系列。長いコマンド実行ログの貼り付けは〔…ログ貼り付け〕と記す。
確定事項は infra/docs/DECISIONS.md（D-78〜D-80）と docs/coding_guides/thinkx_coding_guide.md
「秘密情報は単一の .env に集約する」が正。障害と実測の記録は infra/findings.md 同日分。

> **昨日の作業のあとthinkxinc.comがダウンしているようだ**
> **stagingを停止するまでは少なくとも生きていた　原因を探してくれ**

実測で切り分け: 本番は TCP 接続可・60秒後に LB の nginx が 504(TLS・証明書正常)、staging は接続不能(停止中・意図通り)。lb1・web1 とも running、transformism(8006)・kazukiotsuka(8007)は正常、詰まっているのは thinkx の uwsgi(8005)のみ。uwsgi ログに `remote_control relay state: staging unreachable (ConnectTimeout)` が20秒間隔で連続、`ss` で停止中の staging LB へ SYN-SENT を確認。

原因の連鎖: KOBITO リモコン画面が開きっぱなしのブラウザから5秒ごと(POLL_MS=5000)に /remote_control/state をポーリング → 中継は staging へ timeout=20秒 → 停止中なので毎回20秒詰まる → uwsgi は 1プロセス1スレッドなので全要求が後ろに並び、/ は60秒でLBが504。「stagingを停止するまでは生きていた」はこの構造の説明そのもの。復旧はリモコン画面のタブを閉じるだけ(再起動不要・渋滞でありハングではない)。findings に記録。

---

> **閉じた　しかし設計が悪い　ポーリングし続ける意味があるのか　一度stateが取れたら終了すればいいのでは または5回くらいで取れないなら諦めてサーバーの状態が取得できなかった/止まっている　などの表示に変えるようにしたら？ 開き続けることは余裕でアリエル**

タブクローズ後、本番 200(0.15秒)×3回で回復を実測。改善案として、画面側(取れたら停止+5回で諦め+再確認ボタン)とサーバー側(接続タイムアウト20秒→2秒)を提示。

---

> **それぞれpros/cons どれがいいのか推奨を**

案A(取れたら停止+5回で諦め): 開きっぱなしでもリクエストゼロになり障害構造が根絶。表示がスナップショットになるが操作時に取り直すので実害は小。案B(5回で諦めのみ): 表示は常に最新だが「開きっぱなしで叩き続ける」が半分残る。案C(サーバー側のみ): 設計欠陥そのものは残る。推奨は「案A+サーバー側短縮の両方」— 画面が「意味のあるときだけ聞く」、サーバーが「誰が聞いても詰まらない」の補完関係。行儀のよいクライアントに防御を依存させない意味で本質はサーバー側。

---

> **案A + サーバー側短縮も実施**

実装: index.html の2本の setInterval を廃止し、state は「取れたら停止・503(停止中)も答えとして停止・連続5回失敗で『状態を取得できませんでした』+再確認ボタン」、電源は「確定(起動完了/停止)したら停止・遷移中だけ追う」。main.py は timeout=(2, 従来値) に分離。ローカル静的配信で実測: /state ちょうど5回・/power/state 1回で停止、再確認で5回だけ再試行。pytest 15 passed(route_sweep の1失敗は /filedrop golden のホスト名依存・既存問題で変更前でも同一失敗を実測、thinkx/findings に記録)。コミット2件(5f0532a / f46e0d3)を push。

---

> **残り(反映)**
> **(前ターンの反映手順の引用)**
> **? よくわからない**

言い直し: 直したコードは手元に保存しただけで、動いているサーバー(staging/本番)はまだ古いまま=本番はまだ同じ事故が起きうる。残りは「サーバーに届ける」だけで、staging に届ける(私ができる)→ 本番に届ける(オーナーの実行)の2段。

---

> **デプロイするならコマンド出せよ**

デプロイ手順書(正本)を確認し、手順2(develop へマージ)〜4(staging 確認 URL)〜本番(deploy_production_from_staging.sh)の貼り付けブロックを提示。staging 停止中のため start_staging.sh も含めた。

---

> **stagingを起動していないと本番に反映できないんだっけ？**

スクリプト実装を読んで回答: 技術的には不要。deploy_production_from_staging.sh が触るのは GitHub の origin/develop と本番2台だけで staging には接続しない。「staging で目視確認したものを出す」という運用上の前提があるだけ。(a) staging 確認を飛ばして出す(今回はローカル実測済みでリスク小)/(b) 起動して見てから、の2択を提示し、(a) の場合のコマンド(手順2+本番)を提示。

---

> **cd ~/Sources/thinkx-system**
> **bash infra/scripts/deploy_production_from_staging.sh**
>
> **だったらこれは deploy_production_from_develop.sh が実態ということ？**

その理解が実態に合う。実際の動作は「origin/develop を凍結して本番へ出す」で staging には触れない。"from_staging" は「staging=develop を動かす環境で目視確認した」という前提の表現だが、staging 停止中でも完走するため今回はその前提が成り立っていない。命名規約(操作で命名・唯一の値は名前に書かない)に照らすと deploy_production.sh が整合するが、改名は設計判断なので実行者からは変えない。findings に記録。

---

> **deploy_production_from_developに変えるべきだろ**

改名に着手(git mv+参照置換)した——が、直後にオーナーが本番デプロイを実行中と判明。

---

> **〔deploy_production_from_staging.sh 実行ログ貼り付け — release/2026-09-18 PR #123 マージ・podcast データ配布が進行〕**
> **podcastのstagingでしか使われないデータをアセットとして配っているが配らないデータを指定する仕組みがないのか？**

> **改名はそのあとでいいこっちが先だ**

改名は作業ツリーごと巻き戻し(旧名のまま・再実行安全)。push_assets_podcast.sh を確認: 除外は固定の `_*`/experiments//edit/ のみで、それ以外を全部送るのは D-52 改定「ローカルを完全にコピー」の意図的動作。指定の仕組みは無い。

---

> **このままだとproductionのディスク容量が心配だ**

> **〔続きのログ貼り付け(巨大な wav・backup の転送)〕**
> **とりあえず途中で止めた**

実測: コード反映は deploy-timer が完了済み(uwsgi_thinkx 07:43 UTC 再起動・新コード確認・本番200/remote_control 401)。^C の影響は podcast データの部分コピーのみ(サイズ照合式なので次回続きから)。ローカル data は10G(contents 1.1G・generated 792M・archive 777M・backup 308M・直下生音源約7G)、本番は空き34Gに2.2G転送済み。本番はまだ /podcast/ を配信していない(Phase 4 未着手)。選択肢: (a) Phase 4 まで本番配布停止(推奨) / (b) 環境別で本番は配信物のみ / (c) backup・archive だけ除外 / (d) 現状維持。

---

> **asset配信しないファイルの指定ファイルを作れ　それをasset配布スクリプトは参照して止めろ**
> **指定ファイルは目立つ場所に置け　トップディレクトリ thinkx-system/assets_meta.yaml をサンプルで置いた　参考にしろ　あくまでイメージだ**

> **1 このassetsの問題**
> **2 デプロイスクリプトの改名**
> **3 health check（下記にガイドライン)**
> **が今日やることだ**
> **一個ずつ進めろ**
>
> **サーバーが急に落ちていても気付けないのはまずい．**
> **定期的にhealthチェックをして落ちていたら専用のDiscordチャンネルに通知するようにしたい．専用にするのはこのチェンネルは確実にmuteにしないために他と混ぜるべきでないから．**
> **今staging,production,localの3台を前提としている．lbがもっとも落ちている可能性がないならprod lbからサイトごとのアドレスにcurlまたはhttpを投げて返答を見る仕組みを作るべきだろう．**

assets_meta.yaml を正本化: local(どこにも配らない)/ local_staging(staging には配る・本番には配らない)の2区分。追加確認(生音源 *.wav/*.pkf も本番に配らない・既に本番に入った除外対象は一覧提示のうえ削除)を得て実装。push_assets_podcast.sh が参照し、送る判定と差分照合の両側に同じ除外(再送ループ防止)。判定20ケーステスト合格。本番の既存分約1G削除(2.2G→1.2G・全てローカルに原本)。D-78 記録・コミット 295c71d。オーナーの再実行で「配布0件・一致14件・失敗0件」、本番 3.4G・除外混入0を実測して項目1完了。

---

> **アセットは実行した**

> **できている 次に進もう 3**

項目2(改名)は別スレッド扱いだったセッションが完遂済みと判明(コミット 8eace96・D-79。CLAUDE.md と PODCAST_TRACK.md の旧名参照はオーナー対応、後に「できている」)。項目3に着手したところ、health check の実装ファイル4本(health_check.sh・setup・plist・runbook)が 17:08-17:09 に未コミットで存在するのを発見し、二重実装の衝突として停止・報告。

---

> **こちらで引き取る**
> **ただし仕様は別セッションのほうがいい**
> **別セッションというよりこのセッションで実装したが会話がロールバックされた　つまりこのセッションでの仕事だ**
> **続けよ**

ロールバック前の成果物を引き継ぎ、その仕様(LB=60秒で本番5サイト・Mac launchd=5分で LB と staging[EC2 running のときだけ]・変化時のみ通知+1時間ごと再通知・401=生存)のまま仕上げ。機能試験(down 検知・再通知抑制・復旧通知)と lb1 からの hairpin curl 4サイト200を実測。GUIDELINES 原文・D-80・findings を記録しコミット 0da3b69・develop 取り込み。オーナーへ webhook 作成〜LB 投入〜Mac 投入のコマンド一式を提示。

---

> **〔webhook 作成・テスト・release/2026-09-18-3 実行ログ貼り付け(全サイト200)〕**
> **3までは実行した**

> **/etc/supercom-health.env  ? なるべくレポジトリに入れたいのだがここであるのが良いのか？ 我々はレポジトリに入れてlnさせることをよくする**

webhook URL はリポジトリに入れない(libcommon の webhook 直書きが env 化+ローテーション対象になっている前例)。ただし秘密と一般設定を混ぜていたのは悪く、設定(SITES 等)は git 管理へ、秘密の1行だけ外へ、と分離を提案・実装開始。

---

> **新しい秘密ファイルは作らず既存の .env に相乗りする**
> **Discordのチャンネルは他にも書いてある 単に他と一緒に.envにいれればいいだろ**

lb1 に既存 .env が無いことを実測し、LB は /src/loadbalancer/.env を新設(その箱の最初の .env)、Mac は既存の thinkx/web-server/.env に相乗り、キー名 HEALTH_DISCORD_WEBHOOK_URL(grep で1キーだけ読む・source しない)に変更。

---

> **秘密情報は特別なセキュリティ上の理由がなければ単一の.envに集約する　という原則をコード規約に書くべきだろう**

> **例外(単一 .env に入れない)は特別なセキュリティ上の理由があるときだけで、その理由を**
> **ファイル冒頭に書く。**
> **.envの情報はレポジトリに書き込まない情報を意味する。逆にレポジトリに書き込むべき情報，例えば設定情報は.envでなく.yaml等に書きそれが設定値であることを明示する**
>
> **とさっきのcoding_guidesに書け**

docs/coding_guides/thinkx_coding_guide.md に「秘密情報は単一の .env に集約する」節を新設し、指示原文をそのまま記載(オーナー指示による規範化)。

---

> **=/src/thinkx-system/infra/health/lb.env**
> **なぜ /src/thinkx-system/loadbalancer/.envじゃないんだ？**

2段構えの説明: HEALTH_ENV が指すのは git 管理の設定(秘密なし)、その中の WEBHOOK_ENV が git 外の秘密(.env)を指す。設定まで .env に入れると「リポジトリに入れたい」が崩れる。

---

> **lb.env -> loadbalancer.yaml**
> **ここは設定を書くんだろ？.envとは秘密情報を意味する**

> **mac.env -> local.yaml**

> **health -> health_check**

設定ファイルを YAML 化(infra/health_check/loadbalancer.yaml / local.yaml)、ディレクトリも health_check に改名。スクリプトは HEALTH_CONFIG で YAML を読む素朴な行パース(sites 1段+トップレベルキー・未知キーは WARN)。パースと相乗り .env からの抽出・キー欠落 WARN・down 検知を実測し、コミット 9d60267・develop 取り込み。仕上げのコマンド(release・LB webhook+timer・Mac webhook+launchd)を提示。

---

> **〔LB 投入ログ貼り付け(timer 稼働)と Mac 投入コマンドの実行〕**

LB は 60秒周期で稼働・5サイト up 記録・WARN なしを journal で確認。Mac 側は貼り付け時に webhook URL が2行に割れて .env に入った疑いを検出。さらに通知 curl に --fail が無く「URL 誤りでも成功扱い」になる穴を発見して修正(コミット 4f7d72d)。--fail 後の実弾テストで送信失敗を確認=割れ確定。修正コマンド(URL を短い2変数に分けた折り返し耐性つき)を提示。

---

> **修正コマンドどれ？**

(ブロック再掲。)

> **ok**

実弾テスト: 🔴 down → 🟢 復旧 とも --fail 付きで送達成功(専用チャンネル着弾)。続いて Mac launchd の staging 判定が WARN。原因を実測で特定: /usr/local/bin/aws が存在しない /usr/bin/python を指す残骸で bad interpreter 126。plist の PATH 順変更でも launchd 実プロセスに効かず、最終的に設定 YAML の aws_cli キーでフルパス指定に変更。既定 PATH だけの最小環境と launchd 実機の両方で WARN 0・staging 状態(停止=正常扱い)の記録を実測。コミット 96be98f / f9351fe / 9ed92ed。

---

> **done**

最終確認: LB=60秒×5サイト稼働、Mac=5分で lb+staging、通知経路開通、WARN 0。今日の3項目(assets 除外 D-78・改名 D-79・health check D-80)+障害復旧を完了として報告。残骸 /usr/local/bin/aws の削除はオーナー任意。

---

> **セッションを閉じる いつものやり方で記録して**

本記録を作成。

## 到達点

thinkxinc.com の504はリモコン画面の無限ポーリング×staging停止×uwsgi 1プロセスの合成で、画面の有限化と中継接続2秒化を本番反映して根治。アセット配布は assets_meta.yaml(D-78)で「local / local_staging」の除外指定を正本化し本番から編集中間物・生音源を排除。デプロイスクリプトは実態に合わせ deploy_production_from_develop.sh に改名(D-79)。死活監視は prod LB 60秒+Mac launchd 5分の二段構えで専用 Discord チャンネルに通知する形で稼働開始(D-80)。あわせて「秘密は単一 .env・設定は YAML でリポジトリへ」をコード規約に規範化した。
