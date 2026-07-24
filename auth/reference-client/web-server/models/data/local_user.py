# auth/reference-client/web-server/models/data/local_user.py
#
# Minimal local account record owned by the reference client.

from mongoengine import StringField
from pymongo import ReturnDocument

from libcommon.mongomodel import MongoModel


class LocalUser(MongoModel):
    meta = {'collection': 'reference_local_users'}

    user_id = StringField(required=True, unique=True)
    status = StringField(
        required=True,
        default='active',
        choices=('active', 'disabled'),
    )

    @classmethod
    def ensure(cls, user_id):
        candidate = cls(user_id=user_id, status='active')
        candidate.validate()
        on_insert = candidate.to_mongo().to_dict()
        on_insert.pop('_id', None)
        raw = cls._get_collection().find_one_and_update(
            {'user_id': user_id},
            {'$setOnInsert': on_insert},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return cls._from_son(raw)
