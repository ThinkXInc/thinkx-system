# auth/web-server/models/data/verification_challenge.py
#
# One-time verification state kept separate from permanent User identity data.

from datetime import datetime

from mongoengine import DateTimeField, IntField, StringField
import pytz

from libcommon.mongomodel import MongoModel


class VerificationChallenge(MongoModel):
    meta = {
        'collection': 'verification_challenges',
        'indexes': [{'fields': ['expires_at'], 'expireAfterSeconds': 0}],
    }

    purpose = StringField(
        required=True,
        choices=('signup', 'email_change', 'phone_verification', 'password_reset'),
    )
    channel = StringField(required=True, choices=('email', 'sms'))
    code_hash = StringField(required=True)
    destination = StringField(required=True)
    expires_at = DateTimeField(required=True)
    attempts = IntField(default=0, min_value=0)
    created_at = DateTimeField(default=lambda: datetime.now(pytz.utc))
