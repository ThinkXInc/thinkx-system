#!/usr/bin/env bash
# thinkx-system ワークスペースの初期構築(手順1〜2の自動化)
# 実行場所: ワークスペースを作りたい親ディレクトリ
set -euo pipefail

mkdir -p thinkx-system && cd thinkx-system

# 各リポジトリを clone(親は git 管理しない)
git clone git@github.com:ThinkXInc/simplicity.git
git clone git@github.com:ThinkXInc/libcommon.git
git clone --recurse-submodules git@github.com:ThinkXInc/quantz-web.git  # Track Q は Q-6 まで submodule 状態で作業
git clone git@github.com:ThinkXInc/thinkx.git            # 読み取り専用(消費実態の参照用)
git clone git@github.com:ThinkXInc/kazukiotsukacom.git   # 読み取り専用

mkdir -p docs .claude

echo ""
echo "== 残りの手作業(3ステップ) =="
echo "1. CLAUDE.md / .claude/settings.json / docs/ROADMAP.md をこのディレクトリに配置"
echo "2. 計画書を各リポジトリへ配置:"
echo "     REFACTORING_PLAN.md                  -> simplicity/"
echo "     LIBCOMMON_QUANTZ_REFACTORING_PLAN.md -> libcommon/"
echo "   (ブランチ refactor/2026 の最初のコミットとして各リポジトリにコミットする)"
echo "3. このディレクトリで一度 'claude' を実行してワークスペース信頼を承認してから、"
echo "   'claude --remote-control' で開始"

