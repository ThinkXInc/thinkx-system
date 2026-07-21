# auth/web-server/models/data/connected_service.py
#
# Records that an auth subject has connected to an OAuth/OIDC client.

from datetime import datetime

from mongoengine import DateTimeField, StringField
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
        connected_service, _ = cls.get_or_create(subject=subject, client_id=client_id)
        return connected_service
