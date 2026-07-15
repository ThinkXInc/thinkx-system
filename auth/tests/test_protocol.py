# 契約テスト: protocol.py (純粋モジュール) を外部依存なしで検査する。
# PROTOCOL.md §3 の UserInfo の形をここで凍結する。形が変わればここが落ちる。

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web-server'))

from protocol import (
    PROTOCOL_VERSION, billing_status_of, build_services, build_userinfo,
    with_exchange_token,
)


class StubUser:
    """モデルの正確なフィールド名だけを持つスタブ (別名は存在しない)。"""
    id = '665f1c2ab8e4d21f3c9a7e01'
    email = 'user@example.com'
    email_verified = True
    name = 'Taro Yamada'
    picture_url = 'https://auth.thinkx.com/media/avatars/665f1c2a.png'
    lang = 'ja'
    services = {
        'quantz': {'plan': 'pro', 'stripe_subscription_status': 'active'},
        'podcast': {'plan': 'free', 'stripe_subscription_status': None},
    }


def test_userinfo_has_exactly_the_v1_keys():
    userinfo = build_userinfo(StubUser())
    assert set(userinfo.keys()) == {
        'protocol_version', 'user_id', 'email', 'email_verified',
        'name', 'picture_url', 'locale', 'services',
    }
    assert userinfo['protocol_version'] == PROTOCOL_VERSION == 1
    assert userinfo['user_id'] == '665f1c2ab8e4d21f3c9a7e01'
    assert userinfo['locale'] == 'ja'   # 内部 lang -> ワイヤ locale (境界規則)


def test_services_map_carries_plan_and_rounded_billing_status():
    userinfo = build_userinfo(StubUser())
    assert userinfo['services'] == {
        'quantz': {'plan': 'pro', 'billing_status': 'active'},
        'podcast': {'plan': 'free', 'billing_status': 'none'},
    }
    # 内部の生 Stripe ステータスはワイヤに出ない
    assert 'stripe_subscription_status' not in str(userinfo['services'])


def test_billing_status_is_a_four_value_contract():
    assert billing_status_of('trialing') == 'active'
    assert billing_status_of('unpaid') == 'past_due'
    assert billing_status_of('paused') == 'canceled'
    assert billing_status_of(None) == 'none'
    assert billing_status_of('some_future_stripe_status') == 'none'
    values = {billing_status_of(s) for s in
              ['trialing', 'active', 'past_due', 'unpaid', 'canceled',
               'incomplete', 'incomplete_expired', 'paused', None, '']}
    assert values <= {'none', 'active', 'past_due', 'canceled'}


def test_exchange_fields_are_added_only_by_with_exchange_token():
    userinfo = build_userinfo(StubUser())
    assert 'access_token' not in userinfo and 'expires_in' not in userinfo
    body = with_exchange_token(userinfo, access_token='abc', expires_in=3600)
    assert body['access_token'] == 'abc'
    assert body['expires_in'] == 3600
    assert 'access_token' not in userinfo  # 元の dict を汚さない


def test_empty_services_is_empty_map_not_missing():
    class NewUser(StubUser):
        services = {}
    userinfo = build_userinfo(NewUser())
    assert userinfo['services'] == {}
