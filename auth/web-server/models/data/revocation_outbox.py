# auth/web-server/models/data/revocation_outbox.py
#
# Durable delivery state for auth-to-service session revocation webhooks.

from datetime import datetime

from mongoengine import DateTimeField, DictField, IntField, StringField
import pytz

from libcommon.mongomodel import MongoModel


class RevocationOutbox(MongoModel):
    meta = {
        'collection': 'revocation_outbox',
        'indexes': ['status', 'next_attempt_at'],
    }

    revocation_id = StringField(required=True, unique=True)
    client_id = StringField(required=True)
    payload = DictField(required=True)
    status = StringField(
        required=True,
        default='pending',
        choices=('pending', 'processing', 'delivered'),
    )
    attempts = IntField(default=0, min_value=0)
    next_attempt_at = DateTimeField(default=lambda: datetime.now(pytz.utc))
    processing_started_at = DateTimeField()
    delivered_at = DateTimeField()
    last_error = StringField()
