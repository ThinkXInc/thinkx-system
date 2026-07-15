#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# protocol.py
#
# ThinkX Auth Protocol v1 の UserInfo JSON を組み立てる唯一の場所。
# PROTOCOL.md が仕様、このファイルがその実装。他のどこにも UserInfo を組み立てない。
#
# このモジュールは Flask / MongoEngine / config に依存しない純粋モジュールに保つ
# (契約テストを外部依存なしで走らせるため)。読むのはモデルの正確なフィールド名だけで、
# 別名は読まない (一つの事実に一つの名前)。
#
# 互換性ルール (PROTOCOL.md §6):
#   v1 のフィールドは削除・改名・型変更しない。追加のみ可。
#   破壊的変更は build_userinfo_v2 を新設して並存させる (errors_v1 と同じ思想)。

PROTOCOL_VERSION = 1

# Stripe の生ステータス -> billing_status 4値への丸め。
# 丸める責任を auth のこの一箇所に置き、全サイトを Stripe の仕様から絶縁する。
_STRIPE_TO_BILLING_STATUS = {
    None: 'none',
    '': 'none',
    'trialing': 'active',
    'active': 'active',
    'past_due': 'past_due',
    'unpaid': 'past_due',
    'canceled': 'canceled',
    'incomplete': 'none',
    'incomplete_expired': 'none',
    'paused': 'canceled',
}


def billing_status_of(stripe_status):
    """Stripe subscription status -> protocol の billing_status (4値)"""
    return _STRIPE_TO_BILLING_STATUS.get(stripe_status, 'none')


def build_services(services):
    """User.services の内部表現 -> protocol v1 の services マップ。

    内部表現: { service_id: {'plan': str, 'stripe_subscription_status': str|None} }
    ワイヤ表現: { service_id: {'plan': str, 'billing_status': 4値} }
    """
    services = services or {}
    result = {}
    for service_id, entry in services.items():
        entry = entry or {}
        result[str(service_id)] = {
            'plan': entry.get('plan') or 'free',
            'billing_status': billing_status_of(entry.get('stripe_subscription_status')),
        }
    return result


def build_userinfo(user):
    """User -> protocol v1 の UserInfo dict。

    NOTE: code / message は libcommon の SuccessFormat がレスポンス時に付ける。
    access_token / expires_in は exchange のみなので with_exchange_token で付ける。
    ここは「data 部分」だけを組み立てる。
    """
    return {
        'protocol_version': PROTOCOL_VERSION,

        # OIDC 準拠のワイヤ名。内部フィールドとの対応: lang -> locale (境界規則)
        'user_id': str(user.id),
        'email': user.email,
        'email_verified': bool(user.email_verified),
        'name': user.name or None,
        'picture_url': user.picture_url or None,
        'locale': user.lang,

        # ThinkX 拡張: サービスごとの課金状態。キー一覧が利用可能サービス一覧を兼ねる
        'services': build_services(user.services),
    }


def with_exchange_token(userinfo, access_token, expires_in):
    """exchange のレスポンス専用に access_token / expires_in を追加する。"""
    body = dict(userinfo)
    body['access_token'] = access_token
    body['expires_in'] = int(expires_in)
    return body


def with_protocol_version(error_format):
    """エラーレスポンスに protocol_version を含める (PROTOCOL.md §5)。

    libcommon の APIErrorFormat / ValidationErrorFormat は extra_data を持つので
    そこへ焼き込む。SSO 系ハンドラのエラー返却は必ずこれを通す。
    """
    error_format.extra_data = {
        **(error_format.extra_data or {}),
        'protocol_version': PROTOCOL_VERSION,
    }
    return error_format
