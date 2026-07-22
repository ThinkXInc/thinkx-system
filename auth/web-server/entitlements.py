# auth/web-server/entitlements.py
#
# Auth-internal endpoint for payment-owned billing projection updates.

from datetime import datetime
import hashlib
import hmac
import json

from flask import Blueprint, request
from mongoengine import ValidationError
import pytz

from config import Config, check_config
from libcommon.locale import Locale
from libcommon.web.flask_helpers import (
    content_type_check_json,
    language_wrapper,
    required_fields_check,
    validate_request,
)
from libcommon.web.http_errors import BadRequestAPIErrorFormat, UnauthorizedAPIErrorFormat
from libcommon.web.http_response_formatter import SuccessCode, SuccessFormat
from models.data.service_entitlement import PaymentEventConflictError, ServiceEntitlement
from models.data.auth_service import AuthService
from models.data.user import User
from protocol import with_protocol_version


REQUIRED_KEYS_IN_CONFIG = ['PAYMENT_PROJECTION_WEBHOOK_SECRET']
check_config(Config, REQUIRED_KEYS_IN_CONFIG)
if (
    not Config.PAYMENT_PROJECTION_WEBHOOK_SECRET
    or len(Config.PAYMENT_PROJECTION_WEBHOOK_SECRET.encode('utf-8')) < 32
):
    raise RuntimeError('PAYMENT_PROJECTION_WEBHOOK_SECRET must contain 32+ bytes')

blueprint_entitlements = Blueprint('entitlements', __name__)
locale = Locale('accounts.json')
SIGNATURE_HEADER = 'X-Payment-Signature'


def canonical_projection_body(payload):
    return json.dumps(payload, separators=(',', ':'), sort_keys=True)


def projection_signature(payload):
    signed = f'POST\n/v1/internal/service-entitlements\n{canonical_projection_body(payload)}'
    signature = hmac.new(
        Config.PAYMENT_PROJECTION_WEBHOOK_SECRET.encode('utf-8'),
        signed.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    return f'sha256={signature}'


def valid_projection_signature(payload):
    supplied = request.headers.get(SIGNATURE_HEADER, '')
    return hmac.compare_digest(supplied, projection_signature(payload))


def parse_source_event_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        timestamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        return None
    return timestamp.astimezone(pytz.utc)


@blueprint_entitlements.route('/v1/internal/service-entitlements', methods=['POST'])
@blueprint_entitlements.route(
    '/v1/<lang>/internal/service-entitlements', methods=['POST']
)
@language_wrapper
@content_type_check_json
@required_fields_check([
    'subject',
    'client_id',
    'plan',
    'billing_status',
    'payment_event_id',
    'source_event_timestamp',
])
def update_service_entitlement(lang, lang_name):
    validation_error = validate_request(lang, locale)
    if validation_error:
        return validation_error.http_response()
    payload = request.json
    if not valid_projection_signature(payload):
        error = UnauthorizedAPIErrorFormat(lang=lang, field_name='signature')
        return with_protocol_version(error).http_response()
    source_event_timestamp = parse_source_event_timestamp(
        payload['source_event_timestamp']
    )
    if source_event_timestamp is None:
        error = BadRequestAPIErrorFormat(
            lang=lang, field_name='source_event_timestamp'
        )
        return with_protocol_version(error).http_response()
    if User.objects(subject_id=payload['subject']).first() is None:
        error = BadRequestAPIErrorFormat(lang=lang, field_name='subject')
        return with_protocol_version(error).http_response()
    service = AuthService.find(payload['client_id'])
    if not service or service.status != 'active':
        error = BadRequestAPIErrorFormat(lang=lang, field_name='client_id')
        return with_protocol_version(error).http_response()
    try:
        entitlement, applied = ServiceEntitlement.apply_projection(
            subject=payload['subject'],
            client_id=payload['client_id'],
            plan=payload['plan'],
            billing_status=payload['billing_status'],
            payment_event_id=payload['payment_event_id'],
            source_event_timestamp=source_event_timestamp,
        )
    except PaymentEventConflictError:
        error = BadRequestAPIErrorFormat(lang=lang, field_name='payment_event_id')
        return with_protocol_version(error).http_response()
    except ValidationError:
        error = BadRequestAPIErrorFormat(lang=lang, field_name='billing_status')
        return with_protocol_version(error).http_response()
    return SuccessFormat(
        data={
            'subject': entitlement.subject,
            'client_id': entitlement.client_id,
            'applied': applied,
        },
        code=SuccessCode.OK,
        message=locale.get('entitlement_updated', lang),
    ).http_response()
