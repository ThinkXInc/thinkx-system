# auth/reference-client/web-server/models/data/revocation_receipt.py
#
# Durable idempotency state for auth-to-reference-client revocation delivery.

from datetime import datetime, timedelta
from uuid import uuid4

from mongoengine import DateTimeField, IntField, StringField
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
import pytz

from libcommon.mongomodel import MongoModel


class RevocationReceipt(MongoModel):
    meta = {
        'collection': 'reference_revocation_receipts',
        'indexes': ['status', {'fields': ['revocation_id'], 'unique': True}],
    }

    revocation_id = StringField(required=True)
    issuer = StringField(required=True)
    subject = StringField(required=True)
    auth_generation = IntField(required=True, min_value=0)
    status = StringField(
        required=True,
        choices=('processing', 'completed'),
    )
    claim_token = StringField()
    claimed_at = DateTimeField(required=True)
    completed_at = DateTimeField()

    @classmethod
    def claim(cls, payload, *, now=None, stale_after_seconds=300):
        current_time = now or datetime.now(pytz.utc)
        claim_token = uuid4().hex
        collection = cls._get_collection()
        raw = collection.find_one({'revocation_id': payload['revocation_id']})
        if raw is None:
            candidate = cls(
                revocation_id=payload['revocation_id'],
                issuer=payload['issuer'],
                subject=payload['subject'],
                auth_generation=payload['auth_generation'],
                status='processing',
                claim_token=claim_token,
                claimed_at=current_time,
            )
            candidate.validate()
            on_insert = candidate.to_mongo().to_dict()
            on_insert.pop('_id', None)
            try:
                raw = collection.find_one_and_update(
                    {'revocation_id': payload['revocation_id']},
                    {'$setOnInsert': on_insert},
                    upsert=True,
                    return_document=ReturnDocument.AFTER,
                )
            except DuplicateKeyError:
                raw = collection.find_one(
                    {'revocation_id': payload['revocation_id']}
                )
            receipt = cls._from_son(raw)
            if receipt.claim_token == claim_token:
                return receipt, 'claimed'

        receipt = cls._from_son(raw)
        if receipt.status == 'completed':
            return receipt, 'completed'
        stale_before = current_time - timedelta(seconds=stale_after_seconds)
        recovered = collection.find_one_and_update(
            {
                'revocation_id': payload['revocation_id'],
                'status': 'processing',
                'claimed_at': {'$lte': stale_before},
            },
            {
                '$set': {
                    'claim_token': claim_token,
                    'claimed_at': current_time,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if recovered is not None:
            return cls._from_son(recovered), 'claimed'
        return receipt, 'processing'

    def complete(self, *, now=None):
        current_time = now or datetime.now(pytz.utc)
        raw = self._get_collection().find_one_and_update(
            {
                'revocation_id': self.revocation_id,
                'status': 'processing',
                'claim_token': self.claim_token,
            },
            {
                '$set': {
                    'status': 'completed',
                    'completed_at': current_time,
                },
                '$unset': {'claim_token': ''},
            },
            return_document=ReturnDocument.AFTER,
        )
        return raw is not None

    def abandon(self):
        result = self._get_collection().delete_one({
            'revocation_id': self.revocation_id,
            'status': 'processing',
            'claim_token': self.claim_token,
        })
        return result.deleted_count == 1
