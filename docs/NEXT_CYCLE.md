# 次期サイクル台帳(2026 リファクタリング作戦からの繰延)

Phase 1〜3 の findings と仕分けで「次期送り」と確定した項目の集約。
正本は各リポジトリの findings.md(本表は索引)。着手時は本表を入力に
bugfix_plan と同型の計画を起草する。

| # | 項目 | 出所 | 種別 |
|---|---|---|---|
| 1 | celery.py の非実在モジュール import(live シンボル)— celery の実用途確定時に意味論を設計 | libcommon P3-L7 | 設計判断 |
| 2 | draggable のリスナー解放(F-5 の実害残)。両 setInterval は自己解放済みと監査確認 | simplicity P3-S5 | バグ修正 |
| 3 | PositionMap 一族の再生 or 廃止(F-1/F-2/F-11: MapPointer 不在・Config 取り落とし・未定義変数) | simplicity §1.3 | 機能判断 |
| 4 | Validator.notCorresponding の実装(現状: 消費ゼロ・未実装 TypeError) | simplicity §1.3 | 機能設計 |
| 5 | locale.py の stdlib shadow 根治(モジュールリネーム=全消費先 import 変更) | libcommon N-1 | 破壊的変更 |
| 6 | 残 4×500 ルートの仕分け(TemplateNotFound 2件=デッドルート疑い、データ経路2件) | quantz §1.3(P3-R1 で2件は N-5 波及と判明し 400 化済み) | 機能判断 |
| 7 | flask_helpers の未使用 import 9件(F401 ignore で温存中) | libcommon P3-L3 | 掃除 |
| 8 | スター import の一斉整理(F-6)/ thinkx 独自 flask_helper.py の統合(F-7) | libcommon 既決 | 掃除/統合 |
| 9 | Config の pydantic-settings 化(D-18)/ LESS 凍結→ネイティブ CSS 移行 | 監査時決定 | 任意改善 |
| 10 | コーディングガイド正規化(D-19: 誤変換除去・quantz 反映・公理→契約→リポ→skills 層分解) | Phase 5 前提 | 文書 |
| 11 | F-7 残: _updatePageIndexInBrowswerURL メソッド名 typo(内部一貫・無害) | simplicity §1.3 | 美観 |