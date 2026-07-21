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

import pytest

ROOT = Path(__file__).resolve().parents[1]
SSO = (ROOT / 'web-server' / 'sso.py').read_text()
ACCOUNTS = (ROOT / 'web-server' / 'accounts.py').read_text()
MAIN = (ROOT / 'web-server' / 'main.py').read_text()
CLIENT = (ROOT / 'libcommon_addition' / 'auth_client.py').read_text()
ALL_APP = SSO + ACCOUNTS

# 旧 v1 強制テストに付す共通の skip 理由。
_V1_SKIP = (
    'DECISIONS D-39 / auth-spec: 旧 PROTOCOL v1 前提の規約。OIDC(/oauth/*)ハンドラと衝突するため '
    'skip。auth-spec 準拠の契約テストを A-9(tests/contract, tests/logic)で全面実装して置換する。'
)


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
    assert 'configure_flask_helpers(' in MAIN, 'main.py must call configure_flask_helpers at startup'


# ---------------------------------------------------------------------------
# 旧 PROTOCOL v1 を強制するテスト。OIDC 確定仕様と衝突するため skip。
# A-9 で auth-spec 準拠の契約テストへ置換する。
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason=_V1_SKIP)
def test_every_route_handler_uses_language_wrapper():
    # /oauth/* 標準 endpoint は language_wrapper を持たない(標準 request/response)。
    for decorators, func_name in _handlers(ALL_APP):
        assert '@language_wrapper' in decorators, \
            f'{func_name} lacks @language_wrapper (CLAUDE.md: デコレータ積層)'


@pytest.mark.skip(reason=_V1_SKIP)
def test_every_route_is_registered_with_dual_lang_paths():
    # /oauth/* は言語二重ルートを持たない。
    for decorators, func_name in _handlers(ALL_APP):
        assert decorators.count('.route(') == 2, \
            f'{func_name} must register both /path and /<lang>/path'


@pytest.mark.skip(reason=_V1_SKIP)
def test_post_json_handlers_use_content_type_and_required_fields_decorators():
    # /oauth/token は form-encoded(application/x-www-form-urlencoded)で、JSON 前提の
    # デコレータ積層に乗らない。
    for decorators, func_name in _handlers(ALL_APP):
        if "methods=['POST']" in decorators:
            assert '@content_type_check_json' in decorators, func_name
            assert '@required_fields_check' in decorators, func_name


@pytest.mark.skip(reason=_V1_SKIP)
def test_single_names_no_aliases():
    # exchange_code/exchange_auth_code の別名検査は旧 client 前提。新 client は
    # /oauth/token(code 引き換え)を使う。
    assert "get('secret')" not in ALL_APP
    assert 'X-ThinkX-' not in ALL_APP + CLIENT
    assert 'exchange_code(' not in CLIENT.replace('exchange_auth_code(', '')


@pytest.mark.skip(reason=_V1_SKIP)
def test_protocol_v1_names_are_used_and_old_names_are_absent():
    # 旧 v1 の wire 名(auth_code/service_id/service_secret)を必須とし、標準名
    # (client_id/sub/code)を禁止していた。auth-spec では真逆(標準名を使う)。
    for required in ["'auth_code'", "'service_id'", "'service_secret'"]:
        assert required in SSO and required in CLIENT
    assert 'with_protocol_version(' in SSO
    assert "'protocol_version'" in CLIENT
    for banned in ["'sub'", "'client_id'", "'available_services'",
                   "'picture'\\b", "request.json.get('code')"]:
        assert not re.search(banned, SSO), f'old/banned name in sso.py: {banned}'


@pytest.mark.skip(reason=_V1_SKIP)
def test_single_error_responses_carry_protocol_version():
    # /oauth/* の標準エラーは protocol_version を持たない。
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


@pytest.mark.skip(reason=_V1_SKIP)
def test_userinfo_is_built_only_in_protocol_py():
    # email_verified は /oauth/userinfo で導出値として返るため、app 層での出現禁止は
    # 新仕様と衝突しうる。UserInfo/ID Token 分離の検査は A-9 で作り直す。
    assert "'email_verified':" not in ALL_APP
    assert "'billing_status':" not in ALL_APP


# 旧 JWT/JWKS/refresh_token 禁止は解除済み(banned=[])。auth は OIDC を実装する。
# refresh_token は auth-spec が採用しないため、その不在検査は A-9 の新契約テストで扱う。
def test_no_jwt_or_refresh_token_before_protocol_v2():
    code_only = '\n'.join(
        line for line in ALL_APP.splitlines()
        if not line.strip().startswith('#'))
    for banned in []:
        assert banned not in code_only, banned