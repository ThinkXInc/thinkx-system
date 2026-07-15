# auth 前倒しトラック規約(AUTH_TRACK)

方針(オーナー決定): 根本的な仕様の変更がなく、libcommon 等に後から合わせられるのであれば、
auth のベースを先に作って thinkx-system/auth に配置し、リファクタリングが進んだら
auth をそれに合わせて変更する。スケジュール上、並行作業を優先する。

この前倒しは計画順序の違反ではない。依存を精査した結果に基づく条件付き並列化である:
auth が依存する面のうち PROTOCOL.md(D-9 で凍結)とレスポンス族・locale・validator
([凍結]面)は Phase 2 で動かず、動くのは session / flask_helpers([改修]面)だけであり、
その到達形は libcommon 計画 L-1 に関数シグネチャまで確定している。
つまり吸収すべき差分は「未知の変更」ではなく「既知の・署名まで確定した差分」である。

## 実施の4条件(いずれも必須)

1. **現行 libcommon に対して書く。未来 API の推測を禁止する。**
   `configure_flask_helpers` の import、`Session.configure` の hasattr 探り、など
   L-1 の成果を先取りする投機的コードを書かない(GPT 実装で実際に発生し、
   レビューで検出・除去された失敗モード)。ImportError を握り潰す保険コードも禁止。
2. **auth/CLAUDE.md が実装より先。** デコレータ正順・libcommon の使い方・fail-loudly・
   命名原則(一つの事実に一つの名前。別名 alias の並存禁止)を機械可読にしてから
   実装・統合作業を行う。GPT 事故の根因は「契約は渡ったが作法が渡らなかった」こと。
3. **libcommon の取り込みはスナップショット vendoring。** 現行 master を実物コピーし、
   `VERSION` に `pre-v2.0.0 (master@<短縮sha>)` を記録する。submodule を新規に増やさない。
   スナップショットは編集禁止(settings.json の deny で強制)。修正は原本リポジトリで行う。
4. **Phase 2 完了時の「auth 追随」項目を予約する。** v2.0.0 が出たら (a) bake.sh で
   焼き直し、(b) L-1 の新 API(`Session.configure` / `make_session_helper(user_loader)` /
   `configure_flask_helpers`)への配線替え、(c) auth のテスト一式 green、を1項目として実施
   する(quantz-web の Q-4 と同型の機械的追随)。

## 副次的な利点(記録)

auth は L-1 の注入 API の**2番目の消費者**になる。`make_session_helper` 等の設計が
quantz 専用の形になっていないかを、L-1 の出荷前に実地検証できる。
前倒しは暦の並列であると同時に、Phase 2 の設計検証を兼ねる。

## GPT Pro 実装の扱い(オーナー決定・auth スレッドで確定)

- プロトコル層(protocol.py: 命名準拠・GETDEL・compare_digest・redirect 検証・
  静的ゲートテストの発想)は保持・移植する。
- ハンドラ層は規約(デコレータ積層・libcommon 契約・別名禁止)に従って再構築する。
- 契約に無いもの(/v1/users/me、無文書の service_id パラメータ、全 alias)は捨てる。
- 契約の穴として露呈した点(/v1/users/{user_id} の認証輸送手段)は PROTOCOL.md 側に
  書き足す(実装が契約を勝手に決めない)。

## 未決事項(人間の判断待ち)

- **ファーストバージョンの本番投入時期。** Phase 2 完了(v2.0.0)前に投入する場合、
  条件4の追随が「稼働中サービスの移行」になりコストが一段上がる。
  理想線は「開発は今・投入は v2.0.0 焼き直し後」。投入時期に外部制約があるなら
  追随項目の設計を先に見直すこと。

## セッション規律との関係

auth 実装は独立の作業単位であり、ルート CLAUDE.md の「1セッション=1計画/作業単位」の
規律に入る。simplicity / libcommon の計画セッションと同一セッションで扱わない。
規範は auth/CLAUDE.md + PROTOCOL.md(+ 本文書の4条件)。