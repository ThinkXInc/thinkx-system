# Legacy v1 UserInfo の契約テスト。protocol.py は外部依存なしで検査する。

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web-server'))

from protocol import (
    PROTOCOL_VERSION, billing_status_of, build_userinfo,
    with_exchange_token,
)


class StubUser:
    """モデルの正確なフィールド名だけを持つスタブ (別名は存在しない)。"""
    id = '665f1c2ab8e4d21f3c9a7e01'
    email = 'user@example.com'
    name = 'Taro Yamada'
    picture_url = 'https://auth.thinkx.com/media/avatars/665f1c2a.png'
    lang = 'ja'

    def is_primary_email_verified(self):
        return True


class StubConnection:
    def __init__(self, client_id):
        self.client_id = client_id


class StubEntitlement:
    def __init__(self, client_id, plan, billing_status):
        self.client_id = client_id
        self.plan = plan
        self.billing_status = billing_status


CONNECTED_SERVICES = [StubConnection('quantz'), StubConnection('podcast')]
ENTITLEMENTS = [StubEntitlement('quantz', 'pro', 'active')]


def test_userinfo_has_exactly_the_v1_keys():
    userinfo = build_userinfo(
        StubUser(),
        connected_services=CONNECTED_SERVICES,
        entitlements=ENTITLEMENTS,
    )
    assert set(userinfo.keys()) == {
        'protocol_version', 'user_id', 'email', 'email_verified',
        'name', 'picture_url', 'locale', 'services',
    }
    assert userinfo['protocol_version'] == PROTOCOL_VERSION == 1
    assert userinfo['user_id'] == '665f1c2ab8e4d21f3c9a7e01'
    assert userinfo['locale'] == 'ja'   # 内部 lang -> ワイヤ locale (境界規則)


def test_services_map_carries_plan_and_rounded_billing_status():
    userinfo = build_userinfo(
        StubUser(),
        connected_services=CONNECTED_SERVICES,
        entitlements=ENTITLEMENTS,
    )
    assert userinfo['services'] == {
        'quantz': {'plan': 'pro', 'billing_status': 'active'},
        'podcast': {'plan': 'free', 'billing_status': 'none'},
    }
    assert 'payment_event_id' not in str(userinfo['services'])


def test_billing_status_is_a_four_value_contract():
    assert billing_status_of('active') == 'active'
    assert billing_status_of('past_due') == 'past_due'
    assert billing_status_of('canceled') == 'canceled'
    assert billing_status_of(None) == 'none'
    assert billing_status_of('some_future_stripe_status') == 'none'
    values = {billing_status_of(s) for s in
              ['active', 'past_due', 'canceled', 'none', None, '', 'unknown']}
    assert values <= {'none', 'active', 'past_due', 'canceled'}


def test_exchange_fields_are_added_only_by_with_exchange_token():
    userinfo = build_userinfo(
        StubUser(),
        connected_services=CONNECTED_SERVICES,
        entitlements=ENTITLEMENTS,
    )
    assert 'access_token' not in userinfo and 'expires_in' not in userinfo
    body = with_exchange_token(userinfo, access_token='abc', expires_in=3600)
    assert body['access_token'] == 'abc'
    assert body['expires_in'] == 3600
    assert 'access_token' not in userinfo  # 元の dict を汚さない


def test_empty_services_is_empty_map_not_missing():
    userinfo = build_userinfo(
        StubUser(), connected_services=[], entitlements=[]
    )
    assert userinfo['services'] == {}
