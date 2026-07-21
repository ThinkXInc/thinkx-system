<!-- 配置: thinkx-system/monorepo/docs/CITYWALK_TRACK.md -->

# citywalk 再構築トラック規約(CITYWALK_TRACK)

方針(オーナー決定): 旧 citywalkservers を最新の作り方に合わせて再構築し、monorepo に取り込む。
UI の知覚(見た目・レイアウト・操作反応・文言)は変えず、内部は simplicity / libcommon.web で
作り直す。ビジネスアカウントという概念は廃止し、auth の単一アカウントがユーザー機能とビジネス
機能を兼ねる。画像は PNG より SVG を基本とする。サブディレクトリ名は `citywalk`。
規範は `monorepo/citywalk/refactor_plan.md`。

## 位置づけ(monorepo 移行後の前提)

本トラックは当初 auth トラック(D-25)と同型の「Phase 2 完了待ちの前倒し並行」として設計されたが、
その後ワークスペースは monorepo へ移行し(M トラック)、Phase 2/3/4a/4b は完遂済みとなった。
したがって前提は以下へ転換されている(計画 v2.0 §「v2.0 で何が変わったか」):

- citywalk は clone ではなく monorepo サブディレクトリとして取り込む(M と同型)。
- vendored libcommon / simplicity は **B案(D-35 / COMMON_LIB_POLICY.md)** で運用 —
  canonical v2.1.0 から焼いた編集可能なコピー。旧「編集禁止 deny」は撤回。
- libcommon v2.1.0 は完成・稼働、auth は Phase 4b で追随完了済み。よって「Phase 2 完了待ちの
  追随項目」は不要(計画から削除済み)。citywalk は最初から完成品に直接書く。

## 実施の条件(いずれも必須)

1. **現行 canonical(v2.1.0)に対して書く。未来 API の推測を禁止する。** 実測典拠は monorepo 内の
   既存消費者(thinkx/auth の web-server/libcommon)。
2. **citywalk/CLAUDE.md が実装より先。**(計画 C-0b)
3. **取り込みは M と同型**: 歴史を運ばない(初期化コミット・出所は ARCHIVE.md)、submodule は
   焼き込まず破棄、push 前に M-4 相当の秘密検査。
4. **知覚オラクルを先に建てる(C-0c)**: スクリーンショット回帰 + jsdom 知覚特性テスト。DOM 構造は
   凍結しない(内部表現の自由域)。

## auth との関係(v3.0: OIDC 本格仕様)

auth は OIDC Authorization Code Flow + PKCE(S256) の本格実装に確定した(正本 `monorepo/auth/docs/` 00〜05)。
citywalk は auth の **client(Relying Party)** として、auth/docs 01 の「各サービス(quantz)側」に対応する
実装(ClientTransactionStore / AuthClient / IDTokenVerifier / ServicePrincipal + `/auth/signin`・
`/auth/callback`・`/v1/sessions/revoke`・logout)を作る。新規依存 PyJWT。identity は
`ServicePrincipal(issuer, subject) → local_user_id`。**auth/docs が唯一の正**であり、citywalk は仕様更新に追随する。

## auth との関係(要点)

- citywalk は auth の**サイト統合実装の先行事例**になる(計画 C-5)。Phase 5(quantz-web からの統合)
  より前に citywalk が auth_client・契約テストの実地検証を担う。
- citywalk に独自の資格情報コードを書かない。signup / signin / password 系は auth の管轄。
- auth はローカルインスタンスで結合テストする(D-16 と同じ「本物のインフラ不要」設計)。

## セキュリティ注記(D-22 処理済み)

旧リポジトリの秘匿情報の疑い(旧 public リポ内の Basic 認証資格情報・実証データを含みうる分析
ノート)は計画作成時に人間へ報告済み(計画 §7-1)。対応(旧リポの private 化・無効化・履歴パージ)
は人間の管轄。取り込み側は C-0a の秘密検査(M-4 相当)で門番し、実行者は当該値の転記・移植を
行わない。

## 未決事項(人間の判断待ち)

計画 §7 の 1・3・4・6・7(旧 public リポ対応 / purchase / データ移行 / スタイル統一 / signin 導線化)。
うち §7-4 の裁定前に C-3 へ着手しない。(§7-2 iOS は §1.0「未稼働」で解決、§7-5 リポ名は確定。)

## セッション規律との関係

citywalk 再構築は独立の作業単位であり「1セッション=1計画/作業単位」の規律に入る。
他計画のセッションと同一セッションで扱わない。規範は refactor_plan.md + CLAUDE.md(+ 本文書)。