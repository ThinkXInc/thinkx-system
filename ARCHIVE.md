# ARCHIVE — monorepo 各フォルダの出所

この monorepo は polyrepo + vendoring 構成をファイルコピーで集約したもの(M トラック / `docs/MONOREPO_PLAN.md`)。
**歴史は運んでいない。** 各フォルダのコミット履歴・過去の調査は、下表の旧リポジトリ(凍結アーカイブ)で行う。

取り込み方式: 指定 ref の作業ツリーを `.git` を除いてコピー(無加工)。submodule は実体ファイルとして焼き込み。
SHA・日付は M-2(リポジトリごとの取り込み)で1行ずつ確定・記入する。

| フォルダ | 旧リポジトリ URL | 取り込み ref | HEAD SHA | 取り込み日 |
|---|---|---|---|---|
| `thinkx/` | git@github.com:ThinkXInc/thinkx.git | 2026refactor | `5a621678790b1529c8234ae917e85738f03856b5` | 2026-07-15 |
| `kazukiotsukacom/` | git@github.com:ThinkXInc/kazukiotsukacom.git | 2026refactor | `0ad3809587735f0766e55aec926e83bc7f5690ee` | 2026-07-15 |
| `transformism/` | git@github.com:kazukiotsuka/transformism.git | 2026refactor | `df51b5bb8b67fc6d18056079f0d3fcc3ba61945f` | 2026-07-15 |
| `auth/` | git@github.com:ThinkXInc/auth.git | 2026refactor | `02e97d19976f987d314487fad51c6beed649f986` | 2026-07-15 |
| `infra/` | git@github.com:ThinkXInc/infra.git | 2026refactor | `4ef472643019d8fbe09972a4b0581a7aa2511562` | 2026-07-15 |
| `loadbalancer/` | git@github.com:ThinkXInc/loadbalancer.git | 2026refactor | `5ac8ceb6b917009826884f7c60011cfdef3a6d39` | 2026-07-15 |
| `nginx-web-root/` | git@github.com:ThinkXInc/nginx-web-root.git | 2026refactor | `9214f267b88544daecb8110a7307f3d5bf031d85` | 2026-07-15 |
| `citywalk/` | git@github.com:ThinkXInc/citywalkservers.git | develop | `d54ec193a463974e06bb9a1584845aa55097d548` | 2026-07-20 — 取り込み時に `business.py` / `items.py` の Basic 認証資格情報と `main.py` の Flask secret_key を redact (`citywalk/findings.md` 参照) |

## 取り込み対象外(記録)

- **`libcommon`** — 裁定(2026-07-15・B案 / `docs/COMMON_LIB_POLICY.md`): monorepo にマスターとして
  取り込まない。**原本は独立リポジトリとして monorepo と並置**(`/src/libcommon/.git`)。参照 SHA
  `a316494ff850094b767da041f429092735fd2877`(URL: git@github.com:ThinkXInc/libcommon.git)。
  各サービスは vendored コピー(`*/web-server/libcommon` 等・VERSION 参照)を直接持ち直接編集する。
- **`simplicity`** — 同上(B案)。原本は独立リポジトリとして並置(`/src/simplicity/.git`)。参照 SHA
  `53f0639449a937fe79935175a867689ee4b40a87`(URL: git@github.com:ThinkXInc/simplicity.git)。
- `quantz-web` — 裁定済み: 後続(新システム設計時に判断)。monorepo に含めない。

## submodule の扱い(M-2/M-3/M-4)

- `thinkx/playbooks`(ピン `38bf25aa...`)— M-2 で実体焼き込み後、**M-4 で秘密(VPN PSK 等)を
  含むため monorepo から除外**(`git rm -r thinkx/playbooks`)。`.gitmodules` は M-3 で除去済み。
- `transformism/www/playbooks` — 2026refactor HEAD に gitlink 実体なし(孤立 `.gitmodules`)。
  焼き込む submodule 無し。`.gitmodules` は M-3 で除去済み。
