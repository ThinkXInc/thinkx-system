# PLAN: auth の libcommon v2.0.0 追随 (前倒し実装の回収)

この auth はロードマップ Phase 4 の前倒しとして、libcommon 計画完了前に
pre-v2.0.0 スナップショットに対して建てられた (CLAUDE.md の前倒し条件を参照)。
libcommon v2.0.0 が出荷された時点で、この計画を実行してから本番投入する。
**投入は焼き直し後が原則** (稼働中サービスの移行に格上げしない)。

発動条件: libcommon に v2.0.0 タグ + bake.sh (L-8) が存在すること。
規律: 1項目 = 1コミット。全項目完了 = 全ゲート green が完了定義。

- [ ] **F-1: libcommon v2.0.0 焼き直し。** `scripts/bake_libcommon_snapshot.sh v2.0.0`
      (L-8 の bake.sh が出ていればそちらを使い、このスクリプトを削除する)。
      VERSION が v2.0.0 を指すことを確認。
- [ ] **F-2: session 初期化の追随。** L-1 で `Session.configure(host, port, db)` が
      導入された場合、main.py の RedisSessionInterface 初期化部を新 API へ機械的置換
      (quantz-web Q-4 と同型の作業)。導入されていなければ「対象なし」と記録して閉じる。
- [ ] **F-3: flask_helpers 注入 API の追随。** L-1 の `make_session_helper(user_loader)` は
      auth では未使用のため対象確認のみ。使用箇所が生えていれば置換。
- [ ] **F-4: 全ゲート再実行。** `python3 -m pytest -q tests` green。
      規約ゲート (未来API禁止・別名禁止) が焼き直し後のコードにも通ることを確認。

## ワークスペース側への転記 (状態: 転記済み・番号確定)

前倒しの4条件は **D-25**、GPT 実装の層別扱いは **D-26** として DECISIONS に記録済み。
ROADMAP の Phase 4a/4b 分割・ルート CLAUDE.md の auth 行・libcommon 計画 §1.2 追記も
ワークスペース側セッションで反映済み (方針本体は docs/AUTH_TRACK.md)。

残る修正 (人間が実施): libcommon 計画 v1.5 の変更履歴と §1.2 に「D-24」と
書かれている箇所は **D-25 の誤り** (採番変更前の参照)。次版改訂時に直す。
