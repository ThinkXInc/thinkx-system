# WORKTREES — トラック別 worktree の割当と運用(D-58)

monorepo の並行作業は track ごとの専用 worktree で行う。1 worktree = 1 branch = 1 writer。

## 割当

| track | worktree | branch | 用途 |
|---|---|---|---|
| citywalk | `~/Sources/thinkx-system` | `work/citywalk` | citywalk 再構築(素材の置き場) |
| auth | `~/Sources/thinkx-system-auth` | `work/auth` | auth(OIDC)実装 |
| infra | `~/Sources/thinkx-system-infra` | `work/infra` | I トラック |
| k00bot2 | `~/Sources/thinkx-system-k00bot2` | `k00bot2` | k00bot2 |
| deploy 確認 | `~/Sources/thinkx-system-deploy` | detached | origin の確定 ref を checkout して見るだけ・編集しない |

`~/Sources/thinkx-system` が本体(`.git` の実体)で、他は worktree。

## 規則

- 自分の worktree 以外で `add` / `commit` / `reset` / `rebase` / `clean` / `checkout` / `stash` をしない。
- commit には担当トラックの明示パスだけを含める。`git commit -a` を使わない。
- 別トラックのファイルに変更が必要になったら、そのトラックの worktree へ回す。自分で commit しない。
- Git の変更操作の前に、worktree の絶対パス・branch・HEAD・status を確認する。
- 別セッションが HEAD・index を変更した形跡があれば停止して報告する。
- 共有規約文書(`docs/DECISIONS.md` / `docs/GUIDELINES.md` / `docs/ROADMAP.md`)は追記が競合しやすい。
  競合したら機械的に解決せず、内容を提示して判断を仰ぐ。

## 状態確認

```bash
cd ~/Sources/thinkx-system
git worktree list
git branch -vv
```

## 新しい track の worktree を作る

```bash
cd ~/Sources/thinkx-system
git fetch origin
git worktree add ~/Sources/thinkx-system-<track> -b work/<track> origin/monorepo
```

## 混在した branch を origin 上へ組み直す

別トラックのコミットが祖先に混ざった branch は、reset / rebase で直さない。
origin から新しい branch を作り、自トラックのコミットだけを古い順に cherry-pick する。

```bash
cd ~/Sources/thinkx-system-<track>
git fetch origin
git branch backup/<track>-$(git rev-parse --short HEAD) HEAD
git switch -c work/<track>-clean origin/monorepo
git cherry-pick <自トラックのコミットを古い順に>
```

混入がないことを確認する。

```bash
cd ~/Sources/thinkx-system-<track>
git log --oneline origin/monorepo..HEAD
git diff --stat origin/monorepo..HEAD
```

## デプロイ

デプロイは origin 上の明示的な不変 `DEPLOY_REF`(SHA / タグ)で行う。
ローカル worktree の HEAD・未コミット変更をデプロイ元にしない。
staging で受け入れ確認した `DEPLOY_REF` と完全に同一の ref を production に適用する。
サーバーの deploy checkout は clean に保ち、対話エージェントの編集場所にしない。
