# web-server/tests/golden_utils.py
#
# S2-3 特性ゴールデンの共通基盤(thinkx S-0b と同ドクトリン:
# 初回実測を固定→以降厳密比較)。thinkx/web-server/tests/golden_utils.py と同一ロジック。

import json
import os

GOLDEN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'golden')


def _normalize(obj):
    return json.loads(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str))


def assert_golden(name, actual):
    path = os.path.join(GOLDEN_DIR, name + '.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    actual = _normalize(actual)
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(actual, f, ensure_ascii=False, indent=2, sort_keys=True)
        return
    with open(path, encoding='utf-8') as f:
        expected = json.load(f)
    assert actual == expected, (
        f"golden mismatch: {name}\n  expected={expected}\n  actual={actual}"
    )
