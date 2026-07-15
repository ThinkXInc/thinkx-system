# web-server/tests/test_app_imports.py
#
# S-0b (a): conftest の注入(config_test / boto3 mock)の下で
# `from main import app` が成功することを凍結する。これが vendoring カットオーバー
# (S-1)の import 回帰オラクルの核。

def test_app_imports():
    from main import app
    assert app is not None
    # Flask アプリとして最低限の体裁(ルートが登録されている)
    rules = list(app.url_map.iter_rules())
    assert len(rules) > 0
