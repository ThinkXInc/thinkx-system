# thinkx-system/infra/docs/ClaudeCodeサーバー計画.md
#
# サーバー上に Claude Code を常駐させ、任意のマシンから tmux 経由で編集作業を行う体制。
# 状態: **提案(承認前)**。実行はすべて承認制。
#

## 1. 配置先: supercom-web1-stg(staging の web)1台のみ

理由:
- 編集対象(/src/thinkx-system と各サイト)と実行環境(node v24 / python / uwsgi)が既に揃っている
- 編集 → ビルド → https://staging.<domain>/ での即時確認が同一マシンで完結する(サイト編集フローの想定と一致)
- **prod には置かない**: 本番は「git pull + run スクリプトで反映するだけの箱」を維持する。対話ツールと認証情報を本番に置かない
- lb は編集対象を持たないため対象外

懸念: t3.small(2GB RAM)。Claude Code + フロントビルドの並走でメモリが逼迫したら t3.medium 化(terraform 1行の in-place 変更・承認制)。

## 2. インストール: setup_claude_code.sh を別立て新設

- setup_webserver.sh には入れない(全 web 箱の必須要件ではなく、認証という手作業を含むため)
- `infra/setup/setup_claude_code.sh`(冪等・末尾に色つき verdict):
  前提確認(node v18+ / tmux)→ `npm install -g @anthropic-ai/claude-code` → verify(`claude --version`)
- 構築手順.md には載せない(必須工程でないため)。接続手順は 運用.md に追記する

## 3. 認証

- 初回のみ tmux 内で `claude` を起動して対話ログイン(オーナー実行)。認証情報は /home/kaz/.claude/ に永続
- 認証ファイルは **git にも secrets.tgz にも入れない**(このマシン固有・失われても再ログインで再生成可能)

## 4. tmux 運用

- セッション名は固定で `claude`
- どのマシンからも1コマンドで入る(無ければ作成・あればアタッチ。複数マシン同時アタッチ可):

```
ssh -t supercom-web1-stg 'tmux new -As claude'
```

- 抜けるのはデタッチ(Ctrl-b d)。セッションと Claude Code は残り続ける

## 5. git push の扱い(承認点)

- 現在の deploy key は読み取り専用のため、サーバー上で作った commit を push できない
- **案A(推奨)**: thinkx-system にのみ**書き込み可**の deploy key を新設し、staging web だけに配布する
  (gen_deploy_key.sh で生成 → GitHub 登録時に Allow write access を有効化)
- 案B: サーバーでは commit まで・push は Mac から — 体制の目的(サーバー完結の編集)と矛盾するため非推奨

## 6. 規約との整合

- /src/thinkx-system で起動するため、リポジトリ内の CLAUDE.md / AGENTS.md / .claude/settings.json がそのまま効く
- **サーバー上の Claude Code から terraform は実行しない**: tfvars / state は Mac にのみ存在し、インフラ変更は Mac 側セッションの管轄。破壊操作・secrets のゲートは従来どおり
- Claude Code のメモリ(~/.claude/)はマシン固有で Mac 側と共有されない。共有すべき知見は従来どおり
  リポジトリの GUIDELINES / DECISIONS / findings に書く(それが正本)

## 7. 実行手順(承認後)

1. setup_claude_code.sh を書いて push(Claude)
2. `run $WEB setup_claude_code.sh`(オーナー・staging prerequisites 下で)→ 緑 verdict
3. 案A 承認時: 書き込み deploy key を生成・GitHub 登録・配布(オーナー)
4. tmux 内で claude 初回ログイン(オーナー)
5. 運用.md に接続手順を追記(Claude)

## 承認点

- [ ] 配置先 = staging web 1台のみ(prod に置かない)
- [ ] git push は案A(thinkx-system 限定の書き込み deploy key)でよいか
- [ ] 実行開始のタイミング
