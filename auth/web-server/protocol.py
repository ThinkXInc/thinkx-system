#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# protocol.py
#
# OIDC 置換まで残る legacy v1 の UserInfo JSON を組み立てる唯一の場所。
# 正本は auth-spec と契約テスト。退役予定の PROTOCOL.md を新実装の根拠にしない。
#
# このモジュールは Flask / MongoEngine / config に依存しない純粋モジュールに保つ
# (契約テストを外部依存なしで走らせるため)。読むのはモデルの正確なフィールド名だけで、
# 別名は読まない (一つの事実に一つの名前)。
#
# legacy v1 の互換性ルール:
#   v1 のフィールドは削除・改名・型変更しない。追加のみ可。
#   破壊的変更は build_userinfo_v2 を新設して並存させる (errors_v1 と同じ思想)。

PROTOCOL_VERSION = 1

_BILLING_STATUSES = frozenset({'none', 'active', 'past_due', 'canceled'})


def billing_status_of(projected_status):
    """Payment projection -> protocol billing_status (4 values)."""
    if projected_status in _BILLING_STATUSES:
        return projected_status
    return 'none'


def build_services(connected_services, entitlements):
    """ConnectedService + ServiceEntitlement -> legacy services map."""
    entitlement_by_client = {
        entitlement.client_id: entitlement for entitlement in entitlements
    }
    result = {}
    for connection in connected_services:
        entitlement = entitlement_by_client.get(connection.client_id)
        result[str(connection.client_id)] = {
            'plan': entitlement.plan if entitlement else 'free',
            'billing_status': billing_status_of(
                entitlement.billing_status if entitlement else None
            ),
        }
    return result


def build_userinfo(user, *, connected_services, entitlements):
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
        'email_verified': bool(user.is_primary_email_verified()),
        'name': user.name or None,
        'picture_url': user.picture_url or None,
        'locale': user.lang,

        # ThinkX 拡張: サービスごとの課金状態。キー一覧が利用可能サービス一覧を兼ねる
        'services': build_services(connected_services, entitlements),
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
