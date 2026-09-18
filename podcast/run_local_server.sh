#!/usr/bin/env bash
# 変更系: podcast 編集サイトをローカル(mac)で起動する
#
#   使い方: cd ~/Sources/thinkx-system/podcast
#           . ./run_local_server.sh        (または bash run_local_server.sh)
#           PORT=8011 . ./run_local_server.sh   でポート変更(既定 8010)
#
# 停止は Ctrl+C。source されても呼び出し元シェルを壊さないよう exit / set -e /
# 裸の cd を使わない(docs/coding_guides/bash.md)。

__podcast_here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
if [ ! -x "$__podcast_here/web-server/venv/bin/python" ]; then
  echo "venv がまだ無い。先にこれを実行:"
  echo "  cd $__podcast_here/web-server && python3.11 -m venv venv && venv/bin/pip install -r requirements.txt"
else
  "$__podcast_here/web-server/venv/bin/python" "$__podcast_here/web-server/main.py"
fi
