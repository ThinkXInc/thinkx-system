# auth/reference-client/web-server/models/data/service_principal.py
#
# Atomic mapping from an OIDC identity to one reference-client local user.

from uuid import uuid4

from mongoengine import StringField
from pymongo import ReturnDocument

from libcommon.mongomodel import MongoModel
from models.data.local_user import LocalUser


class ServicePrincipal(MongoModel):
    meta = {
        'collection': 'reference_service_principals',
        'indexes': [{'fields': ['issuer', 'subject'], 'unique': True}],
    }

    issuer = StringField(required=True)
    subject = StringField(required=True)
    local_user_id = StringField(required=True)

    @classmethod
    def find_one(cls, *, issuer, subject):
        return cls.objects(issuer=issuer, subject=subject).first()

    @classmethod
    def find_or_create(cls, *, issuer, subject):
        candidate = cls(
            issuer=issuer,
            subject=subject,
            local_user_id=uuid4().hex,
        )
        candidate.validate()
        on_insert = candidate.to_mongo().to_dict()
        on_insert.pop('_id', None)
        raw = cls._get_collection().find_one_and_update(
            {'issuer': issuer, 'subject': subject},
            {'$setOnInsert': on_insert},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        principal = cls._from_son(raw)
        LocalUser.ensure(principal.local_user_id)
        return principal
