# auth/web-server/revocation.py
#
# Durable global revocation and signed service-webhook delivery.

from datetime import datetime, timedelta
import hashlib
import hmac
import json
from uuid import uuid4

import pytz
import requests
from pymongo import ReturnDocument

from config import Config
from libcommon.web.session import Session
from models.data.auth_service import AuthService
from models.data.connected_service import ConnectedService
from models.data.revocation_outbox import RevocationOutbox


WEBHOOK_PATH = '/v1/sessions/revoke'


def canonical_webhook_body(payload):
    return json.dumps(payload, separators=(',', ':'), sort_keys=True)


def webhook_signature(secret, payload):
    signed = f'POST\n{WEBHOOK_PATH}\n{canonical_webhook_body(payload)}'
    digest = hmac.new(
        secret.encode('utf-8'), signed.encode('utf-8'), hashlib.sha256
    ).hexdigest()
    return f'sha256={digest}'


def revoke_user(user, reason):
    user.auth_generation += 1
    user.save()
    Session.revoke_all(str(user.id))
    issued_at = int(datetime.now(pytz.utc).timestamp())
    for connection in ConnectedService.objects(subject=user.subject_id):
        service = AuthService.find(connection.client_id)
        if not service or not service.revoke_url or not service.revoke_webhook_secret:
            continue
        revocation_id = str(uuid4())
        payload = {
            'issuer': Config.AUTH_PUBLIC_BASE_URL.rstrip('/'),
            'subject': user.subject_id,
            'auth_generation': user.auth_generation,
            'reason': reason,
            'revocation_id': revocation_id,
            'issued_at': issued_at,
        }
        RevocationOutbox(
            revocation_id=revocation_id,
            client_id=service.client_id,
            payload=payload,
        ).save()
    return user.auth_generation


def deliver_outbox_record(record, post=requests.post):
    service = AuthService.find(record.client_id)
    if not service or not service.revoke_url or not service.revoke_webhook_secret:
        record.status = 'pending'
        record.processing_started_at = None
        record.attempts += 1
        record.last_error = 'service revocation configuration unavailable'
        record.next_attempt_at = datetime.now(pytz.utc) + timedelta(minutes=5)
        record.save()
        return False
    try:
        response = post(
            service.revoke_url,
            data=canonical_webhook_body(record.payload),
            headers={
                'Content-Type': 'application/json',
                'X-Auth-Signature': webhook_signature(
                    service.revoke_webhook_secret, record.payload
                ),
            },
            timeout=(3.0, 10.0),
            allow_redirects=False,
        )
        if not 200 <= response.status_code < 300:
            raise requests.HTTPError(f'HTTP {response.status_code}')
    except requests.RequestException as error:
        record.status = 'pending'
        record.processing_started_at = None
        record.attempts += 1
        record.last_error = type(error).__name__
        record.next_attempt_at = datetime.now(pytz.utc) + timedelta(minutes=5)
        record.save()
        return False
    record.status = 'delivered'
    record.processing_started_at = None
    record.attempts += 1
    record.delivered_at = datetime.now(pytz.utc)
    record.last_error = None
    record.save()
    return True


def deliver_pending_revocations(post=requests.post):
    now = datetime.now(pytz.utc)
    stale_processing_time = now - timedelta(minutes=5)
    results = []
    collection = RevocationOutbox._get_collection()
    while True:
        raw = collection.find_one_and_update(
            {
                '$or': [
                    {'status': 'pending', 'next_attempt_at': {'$lte': now}},
                    {
                        'status': 'processing',
                        'processing_started_at': {'$lte': stale_processing_time},
                    },
                ],
            },
            {'$set': {'status': 'processing', 'processing_started_at': now}},
            sort=[('next_attempt_at', 1)],
            return_document=ReturnDocument.AFTER,
        )
        if raw is None:
            return results
        results.append(
            deliver_outbox_record(RevocationOutbox._from_son(raw), post=post)
        )
