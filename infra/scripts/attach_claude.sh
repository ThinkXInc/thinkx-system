#!/usr/bin/env bash
# thinkx-system/infra/scripts/attach_claude.sh   【分類: 観測系(接続するだけ・状態を変えない)】
#
# サーバー上の Claude Code セッション(tmux)に入る。無ければ作成・あればアタッチ(複数マシン同時可)。
# 対象は staging の web 固定(prod には置かない — docs/サーバー編集のエージェント化計画.md 1章)。
# 抜けるのはデタッチ(Ctrl-b d)。セッションと Claude Code は残り続ける。
#
#   使い方: bash infra/scripts/attach_claude.sh

exec ssh -t supercom-web1-stg 'tmux new -As claude'
