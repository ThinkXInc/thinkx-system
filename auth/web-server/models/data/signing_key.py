# auth/web-server/models/data/signing_key.py
#
# RS256 signing keys and their publication lifecycle.

from datetime import datetime

from mongoengine import (
    DateTimeField,
    DoesNotExist,
    MultipleObjectsReturned,
    NotUniqueError,
    StringField,
)
import pytz

from libcommon.mongomodel import MongoModel


class ActiveSigningKeyNotFoundError(RuntimeError):
    pass


class ActiveSigningKeyInvariantError(RuntimeError):
    pass


class SigningKey(MongoModel):
    meta = {
        'collection': 'signing_keys',
        'indexes': [{
            'fields': ['status'],
            'unique': True,
            'partialFilterExpression': {'status': 'active'},
        }],
    }

    kid = StringField(required=True, unique=True)
    public_key = StringField(required=True)
    private_key = StringField(required=True)
    status = StringField(
        required=True,
        choices=('active', 'next', 'retiring', 'retired'),
    )
    created_at = DateTimeField(default=lambda: datetime.now(pytz.utc))

    @classmethod
    def get_active(cls):
        try:
            return cls.objects.get(status='active')
        except DoesNotExist as error:
            raise ActiveSigningKeyNotFoundError() from error
        except MultipleObjectsReturned as error:
            raise ActiveSigningKeyInvariantError(
                'More than one active signing key exists'
            ) from error

    @classmethod
    def ensure_active(cls, *, kid, public_key, private_key):
        try:
            return cls.get_active()
        except ActiveSigningKeyNotFoundError:
            try:
                return cls(
                    kid=kid,
                    public_key=public_key,
                    private_key=private_key,
                    status='active',
                ).save()
            except NotUniqueError:
                return cls.get_active()
