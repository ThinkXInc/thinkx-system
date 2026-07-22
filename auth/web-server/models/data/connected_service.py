# auth/web-server/models/data/connected_service.py
#
# Records that an auth subject has connected to an OAuth/OIDC client.

from datetime import datetime

from mongoengine import DateTimeField, StringField
from pymongo import ReturnDocument
import pytz

from libcommon.mongomodel import MongoModel


class ConnectedService(MongoModel):
    meta = {
        'collection': 'connected_services',
        'indexes': [{'fields': ['subject', 'client_id'], 'unique': True}],
    }

    subject = StringField(required=True)
    client_id = StringField(required=True)
    connected_at = DateTimeField(default=lambda: datetime.now(pytz.utc))

    @classmethod
    def connect(cls, subject, client_id):
        candidate = cls(subject=subject, client_id=client_id)
        candidate.validate()
        on_insert = candidate.to_mongo().to_dict()
        on_insert.pop('_id', None)
        raw = cls._get_collection().find_one_and_update(
            {'subject': subject, 'client_id': client_id},
            {'$setOnInsert': on_insert},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return cls._from_son(raw)
