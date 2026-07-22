# auth/web-server/models/data/service_entitlement.py
#
# Read-only billing projection pushed from the payment service.

from datetime import datetime

from mongoengine import DateTimeField, StringField
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
import pytz

from libcommon.mongomodel import MongoModel


BILLING_STATUSES = ('none', 'active', 'past_due', 'canceled')


class PaymentEventConflictError(RuntimeError):
    pass


def as_utc(timestamp):
    if timestamp.tzinfo is None:
        return pytz.utc.localize(timestamp)
    return timestamp.astimezone(pytz.utc)


def as_bson_utc(timestamp):
    timestamp = as_utc(timestamp)
    return timestamp.replace(microsecond=(timestamp.microsecond // 1000) * 1000)


class ServiceEntitlement(MongoModel):
    meta = {
        'collection': 'service_entitlements',
        'indexes': [
            {'fields': ['subject', 'client_id'], 'unique': True},
            {'fields': ['payment_event_id'], 'unique': True},
        ],
    }

    subject = StringField(required=True)
    client_id = StringField(required=True)
    plan = StringField(required=True)
    billing_status = StringField(required=True, choices=BILLING_STATUSES)
    payment_event_id = StringField(required=True)
    source_event_timestamp = DateTimeField(required=True)
    updated_at = DateTimeField(default=lambda: datetime.now(pytz.utc))

    @classmethod
    def apply_projection(
        cls, *, subject, client_id, plan, billing_status, payment_event_id,
        source_event_timestamp
    ):
        source_event_timestamp = as_bson_utc(source_event_timestamp)
        cls(
            subject=subject,
            client_id=client_id,
            plan=plan,
            billing_status=billing_status,
            payment_event_id=payment_event_id,
            source_event_timestamp=source_event_timestamp,
        ).validate()
        collection = cls._get_collection()

        while True:
            now = as_bson_utc(datetime.now(pytz.utc))
            try:
                raw = collection.find_one_and_update(
                    {
                        'subject': subject,
                        'client_id': client_id,
                        'payment_event_id': {'$ne': payment_event_id},
                        '$or': [
                            {
                                'source_event_timestamp': {
                                    '$lt': source_event_timestamp,
                                },
                            },
                            {
                                'source_event_timestamp': source_event_timestamp,
                                'payment_event_id': {'$lt': payment_event_id},
                            },
                            {'source_event_timestamp': {'$exists': False}},
                        ],
                    },
                    {
                        '$set': {
                            'subject': subject,
                            'client_id': client_id,
                            'plan': plan,
                            'billing_status': billing_status,
                            'payment_event_id': payment_event_id,
                            'source_event_timestamp': source_event_timestamp,
                            'updated_at': now,
                            'updated': now,
                        },
                        '$setOnInsert': {'created': now},
                    },
                    upsert=True,
                    return_document=ReturnDocument.AFTER,
                )
                return cls._from_son(raw), True
            except DuplicateKeyError:
                duplicate = collection.find_one(
                    {'payment_event_id': payment_event_id}
                )
                if duplicate is not None:
                    duplicate_timestamp = as_utc(
                        duplicate['source_event_timestamp']
                    )
                    if (
                        duplicate['subject'] == subject
                        and duplicate['client_id'] == client_id
                        and duplicate['plan'] == plan
                        and duplicate['billing_status'] == billing_status
                        and duplicate_timestamp == source_event_timestamp
                    ):
                        return cls._from_son(duplicate), False
                    raise PaymentEventConflictError(
                        f'payment_event_id {payment_event_id} has conflicting data'
                    )

                current = collection.find_one(
                    {'subject': subject, 'client_id': client_id}
                )
                if (
                    current is not None
                    and (
                        as_utc(current['source_event_timestamp']),
                        current['payment_event_id'],
                    )
                    >= (source_event_timestamp, payment_event_id)
                ):
                    return cls._from_son(current), False

                # Equal timestamps use event id as a deterministic tie-breaker.
                # Retry only when a competing writer left a lower ordering key.
