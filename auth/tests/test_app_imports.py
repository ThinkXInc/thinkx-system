# auth の app が、テスト用 config (mongomock / fakeredis) の下で import 可能であることを確認する。
# これが通ることは「起動可能な足場」が成立している最小の証拠。機能は検証しない。
# monkeypatch は tests/conftest.py が main の import 前に行う。


def test_app_is_importable_under_test_config():
    from main import app
    assert app is not None


def test_core_blueprints_are_registered():
    from main import app
    assert 'sso' in app.blueprints
    assert 'accounts' in app.blueprints


def test_google_oauth_client_id_is_injected_at_startup():
    from config import Config
    from libcommon.web import google_oauth_helper
    import main  # noqa: F401

    assert google_oauth_helper._client_id == Config.GOOGLE_OAUTH_CLIENT_ID


def test_healthcheck_route_exists():
    from main import app
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert '/healthcheck' in rules


def test_session_helper_is_wired_via_injection():
    # L-1 (v2.0.0) 追随: make_session_helper に auth 自身の User 取得と例外を注入した
    # session_helper が組めること (auth は L-1 注入 API の 2 番目の消費者)。
    import app_session
    assert callable(app_session.session_helper)
    # 注入した decorator が関数を包めること (make_session_helper が auth の注入を受理した証拠)。
    wrapped = app_session.session_helper(lambda user: user)
    assert callable(wrapped)
