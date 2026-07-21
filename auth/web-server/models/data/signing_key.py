# auth/web-server/models/data/signing_key.py
#
# RS256 signing keys and their publication lifecycle.

from datetime import datetime

from mongoengine import DateTimeField, StringField
import pytz

from libcommon.mongomodel import MongoModel


class SigningKey(MongoModel):
    meta = {'collection': 'signing_keys'}

    kid = StringField(required=True, unique=True)
    public_key = StringField(required=True)
    private_key = StringField(required=True)
    status = StringField(
        required=True,
        choices=('active', 'next', 'retiring', 'retired'),
    )
    created_at = DateTimeField(default=lambda: datetime.now(pytz.utc))
