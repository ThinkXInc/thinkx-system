# 規約ゲート: CLAUDE.md の「禁止事項」「ハンドラの書き方」をソースに対して静的に検査する。
# 規約を散文で終わらせず機械化する (発想は GPT 実装の静的テストから継承し、対象を拡張した)。
#
# 【2026-07 更新 / DECISIONS D-38・D-39・auth-spec】
# 本ファイルは元々、旧 PROTOCOL.md v1 を機械的に強制していた。auth は OIDC(Authorization Code
# Flow + PKCE)へ確定したため、旧 v1 を強制するテスト(wire 名 service_id/auth_code の強制、
# 全ルートへの language_wrapper/二重ルート/protocol_version の強制、'client_id'/'sub' の禁止 等)は
# 確定仕様の /oauth/* ハンドラと正面衝突する。
#
# 方針:
#   - 旧 v1 強制テストは skip する(削除ではなく skip。理由に D-39 を明記)。
#     auth-spec 準拠の新契約テストは tests/contract/ ・ tests/logic/ に A-9 で全面実装する。
#   - 通常 account API に生きる規約(私設ヘルパ禁止・別名禁止・ImportError 保険禁止・
#     L-1 注入 API 配線検査)は維持する。
#   - どのテストを skip しどれを維持するかの最終線引きは、A 計画着手時に findings へ記録する。

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SSO = (ROOT / 'web-server' / 'sso.py').read_text()
ACCOUNTS = (ROOT / 'web-server' / 'accounts.py').read_text()
MAIN = (ROOT / 'web-server' / 'main.py').read_text()
CLIENT = (ROOT / 'libcommon_addition' / 'auth_client.py').read_text()
OIDC = (ROOT / 'web-server' / 'oidc' / 'endpoints.py').read_text()
ID_TOKEN = (ROOT / 'web-server' / 'oidc' / 'id_token.py').read_text()
ALL_APP = SSO + ACCOUNTS


def _handlers(source):
    """route デコレータ直後のブロックを (デコレータ列, 関数名) で列挙する。"""
    blocks = re.findall(
        r'((?:@blueprint_\w+\.route\([^\n]*\)\n)+(?:@\w+[^\n]*\n)*)def (\w+)\(',
        source)
    return blocks


# ---------------------------------------------------------------------------
# 維持する規約(通常 account API / 横断的な安全規約)。auth-spec でも有効。
# ---------------------------------------------------------------------------

def test_no_private_validation_or_error_framework():
    for banned in ['def _api_error', 'def _required(', 'def _message(',
                   'get_json(silent=True)', '_require_json_fields']:
        assert banned not in ALL_APP, f'private helper forbidden: {banned}'


def test_no_import_error_insurance_or_api_probing():
    # AUTH_TRACK 条件1 の恒久部分: 未来 API を握り潰す保険コード (except ImportError) と
    # hasattr での API 探りは禁止。
    for banned in ['except ImportError', 'hasattr(Session', 'hasattr(session_module']:
        assert banned not in ALL_APP + MAIN + CLIENT, f'insurance/probe code forbidden: {banned}'


def test_l1_injection_apis_are_wired_in_main():
    # L-1 追随: 新初期化 API が main.py で app 起動時に注入されていること。
    assert 'Session.configure(' in MAIN, 'main.py must call Session.configure at startup'
    assert MAIN.count('prefix=Config.REDIS_SESSION_KEY_PREFIX') == 2
    assert 'configure_flask_helpers(' in MAIN, 'main.py must call configure_flask_helpers at startup'


# ---------------------------------------------------------------------------
# auth-spec / OIDC の正本契約。旧 PROTOCOL v1 の7 skipをA-9で置換した。
# ---------------------------------------------------------------------------

def test_oidc_routes_are_single_standard_paths_without_language_wrapper():
    expected_routes = (
        "get('/oauth/authorize')",
        "post('/oauth/token')",
        "route('/oauth/userinfo', methods=['GET', 'POST'])",
        "post('/oauth/logout')",
        "get('/.well-known/openid-configuration')",
        "get('/oauth/jwks')",
    )
    for route in expected_routes:
        assert route in OIDC
    assert '/<lang>/oauth/' not in OIDC
    assert '@language_wrapper' not in OIDC


def test_account_json_post_handlers_keep_common_decorator_stack():
    for decorators, func_name in _handlers(ACCOUNTS):
        if "methods=['POST']" not in decorators:
            continue
        assert '@language_wrapper' in decorators, func_name
        assert decorators.count('.route(') == 2, func_name
        assert '@content_type_check_json' in decorators, func_name
        assert '@required_fields_check' in decorators, func_name


def test_token_endpoint_uses_standard_form_contract():
    assert "request.mimetype != 'application/x-www-form-urlencoded'" in OIDC
    for name in ('grant_type', 'code', 'redirect_uri', 'code_verifier'):
        assert repr(name) in OIDC
    assert 'request.get_json' not in OIDC


def test_oidc_uses_canonical_names_without_private_aliases():
    for required in ("'client_id'", "'sub'", "'code'", "'access_token'"):
        assert required in OIDC
    assert 'X-ThinkX-' not in OIDC
    assert "'protocol_version'" not in OIDC
    assert "'auth_code'" not in OIDC
    assert "'service_id'" not in OIDC


def test_oauth_errors_use_standard_error_shape_without_legacy_wrapper():
    assert "jsonify({'error': error})" in OIDC
    assert 'with_protocol_version' not in OIDC
    assert 'APIErrorFormat' not in OIDC


def test_id_token_and_userinfo_claim_responsibilities_are_separate():
    for claim in ("'iss'", "'sub'", "'aud'", "'exp'", "'iat'", "'nonce'"):
        assert claim in ID_TOKEN
    assert "'email'" not in ID_TOKEN
    assert "'email_verified'" not in ID_TOKEN
    assert "claims['email']" in OIDC
    assert "claims['email_verified']" in OIDC
    assert 'billing_status' not in OIDC + ID_TOKEN


def test_refresh_token_is_not_part_of_initial_oidc_contract():
    code_only = '\n'.join(
        line for line in (OIDC + ID_TOKEN).splitlines()
        if not line.strip().startswith('#')
    )
    assert 'refresh_token' not in code_only
