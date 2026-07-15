# web-server/tests/test_app_imports.py
#
# S2-3 (a): conftest の注入(config_test / boto3 mock)の下で
# `from main import app` が成功することを凍結する。vendoring カットオーバー(S2-2)後の
# import 回帰オラクル。thinkx/web-server/tests/test_app_imports.py と同一ロジック。

def test_app_imports():
    from main import app
    assert app is not None
    # Flask アプリとして最低限の体裁(ルートが登録されている)
    rules = list(app.url_map.iter_rules())
    assert len(rules) > 0
