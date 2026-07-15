# web-server/tests/conftest.py
#
# S-0b: kazukiotsukacom をテストプロセスで import 可能にする配線(quantz Q-1 と同型の縮小版)。
# main.py は import 時に (1) config 検査、(2) libcommon.mail が boto3 SES クライアントを生成
# する。そのままでは import できない/実ネットワーク I/O が走るため、main import より前に:
#   1) config 注入: sys.modules['config'] = config_test(全必須キーを埋めたテスト用 Config)。
#      本番 config.py は編集しない(src 変更ゼロ)。
#   2) boto3 を no-op mock に(mails/send_mail.py が import 時に libcommon.mail.Mail() を生成し
#      boto3.client('ses', ...) を呼ぶため。実 AWS 呼出を遮断)。
#
# 本サイトは mongo / redis / session を使わない(消費面は libcommon の[凍結]面のみ)。
# 必要になった事実は findings.md に記録する。

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))       # web-server/tests
_WEBSERVER = os.path.dirname(_HERE)                       # web-server

for _p in (_HERE, _WEBSERVER):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 本番は web-server/ を cwd に起動する(jinja loader が 'views/templates' の相対パス)。
# テストをどこから起動しても本番同等にテンプレ解決できるよう cwd を web-server に固定する。
os.chdir(_WEBSERVER)

# 1) config 注入(最初に。以降の `from config import ...` は全てこれを掴む)
import config_test
sys.modules['config'] = config_test

# 2) boto3 -> no-op mock
import boto3
from unittest.mock import MagicMock

boto3.client = lambda *args, **kwargs: MagicMock()
boto3.resource = lambda *args, **kwargs: MagicMock()
