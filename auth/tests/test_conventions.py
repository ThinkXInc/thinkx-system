# 規約ゲート: CLAUDE.md の「禁止事項」「ハンドラの書き方」をソースに対して静的に検査する。
# 規約を散文で終わらせず機械化する (発想は GPT 実装の静的テストから継承し、対象を拡張した)。

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SSO = (ROOT / 'web-server' / 'sso.py').read_text()
ACCOUNTS = (ROOT / 'web-server' / 'accounts.py').read_text()
MAIN = (ROOT / 'web-server' / 'main.py').read_text()
CLIENT = (ROOT / 'libcommon_addition' / 'auth_client.py').read_text()
ALL_APP = SSO + ACCOUNTS


def _handlers(source):
    """route デコレータ直後のブロックを (デコレータ列, 関数名) で列挙する。"""
    blocks = re.findall(
        r'((?:@blueprint_\w+\.route\([^\n]*\)\n)+(?:@\w+[^\n]*\n)*)def (\w+)\(',
        source)
    return blocks


def test_every_route_handler_uses_language_wrapper():
    for decorators, func_name in _handlers(ALL_APP):
        assert '@language_wrapper' in decorators, \
            f'{func_name} lacks @language_wrapper (CLAUDE.md: デコレータ積層)'


def test_every_route_is_registered_with_dual_lang_paths():
    for decorators, func_name in _handlers(ALL_APP):
        assert decorators.count('.route(') == 2, \
            f'{func_name} must register both /path and /<lang>/path'


def test_post_json_handlers_use_content_type_and_required_fields_decorators():
    for decorators, func_name in _handlers(ALL_APP):
        if "methods=['POST']" in decorators:
            assert '@content_type_check_json' in decorators, func_name
            assert '@required_fields_check' in decorators, func_name


def test_no_private_validation_or_error_framework():
    for banned in ['def _api_error', 'def _required(', 'def _message(',
                   'get_json(silent=True)', '_require_json_fields']:
        assert banned not in ALL_APP, f'private helper forbidden: {banned}'


def test_no_import_error_insurance_or_api_probing():
    # AUTH_TRACK 条件1 の恒久部分: 未来 API を握り潰す保険コード (except ImportError) と
    # hasattr での API 探りは v2.0.0 追随後も禁止。configure_flask_helpers / Session.configure
    # は v2.0.0 で実在 API になったため投機ではなくなり、下の test で「配線済み」を正に検査する。
    for banned in ['except ImportError', 'hasattr(Session', 'hasattr(session_module']:
        assert banned not in ALL_APP + MAIN + CLIENT, f'insurance/probe code forbidden: {banned}'


def test_l1_injection_apis_are_wired_in_main():
    # L-1 (v2.0.0) 追随: 新初期化 API が main.py で app 起動時に注入されていること。
    assert 'Session.configure(' in MAIN, 'main.py must call Session.configure at startup'
    assert 'configure_flask_helpers(' in MAIN, 'main.py must call configure_flask_helpers at startup'


def test_single_names_no_aliases():
    # 同じ値に対する複数の名前 (別名) の禁止
    assert "get('secret')" not in ALL_APP
    assert 'X-ThinkX-' not in ALL_APP + CLIENT
    assert 'exchange_code(' not in CLIENT.replace('exchange_auth_code(', '')


def test_protocol_v1_names_are_used_and_old_names_are_absent():
    for required in ["'auth_code'", "'service_id'", "'service_secret'"]:
        assert required in SSO and required in CLIENT
    assert 'with_protocol_version(' in SSO      # 単体エラーへの焼き込み機構
    assert "'protocol_version'" in CLIENT       # 消費側の検査
    for banned in ["'sub'", "'client_id'", "'available_services'",
                   "'picture'\\b", "request.json.get('code')"]:
        assert not re.search(banned, SSO), f'old/banned name in sso.py: {banned}'


def test_single_error_responses_carry_protocol_version():
    # 名前付きエラークラスの返却は必ず with_protocol_version を通す
    for source, fname in [(SSO, 'sso.py'), (ACCOUNTS, 'accounts.py')]:
        for match in re.finditer(r'(\w+APIErrorFormat|\w+ErrorFormat)\(', source):
            name = match.group(1)
            if name in ('APIErrorFormat', 'ValidationErrorFormat'):
                continue
            line_start = source.rfind('\n', 0, match.start())
            region = source[max(0, line_start - 120):match.start()]
            assert ('with_protocol_version' in region
                    or 'error = ' in source[line_start:match.start()]), \
                f'{fname}: {name} must go through with_protocol_version'


def test_userinfo_is_built_only_in_protocol_py():
    # UserInfo 固有キーの手組みが app 層に無いこと (組み立ては protocol.py だけ)
    assert "'email_verified':" not in ALL_APP
    assert "'billing_status':" not in ALL_APP


def test_no_jwt_or_refresh_token_before_protocol_v2():
    code_only = '\n'.join(
        line for line in ALL_APP.splitlines()
        if not line.strip().startswith('#'))
    for banned in ['import jwt', 'jwks', 'JWKS', 'refresh_token']:
        assert banned not in code_only, banned
