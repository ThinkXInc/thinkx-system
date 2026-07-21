# auth/web-server/models/data/service_entitlement.py
#
# Read-only billing projection pushed from the payment service.

from datetime import datetime

from mongoengine import DateTimeField, StringField
import pytz

from libcommon.mongomodel import MongoModel


def as_utc(timestamp):
    if timestamp.tzinfo is None:
        return pytz.utc.localize(timestamp)
    return timestamp.astimezone(pytz.utc)


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
    billing_status = StringField(required=True)
    payment_event_id = StringField(required=True)
    source_event_timestamp = DateTimeField(required=True)
    updated_at = DateTimeField(default=lambda: datetime.now(pytz.utc))

    @classmethod
    def apply_projection(
        cls, *, subject, client_id, plan, billing_status, payment_event_id,
        source_event_timestamp
    ):
        existing_event = cls.objects(payment_event_id=payment_event_id).first()
        if existing_event:
            return existing_event, False

        entitlement = cls.objects(subject=subject, client_id=client_id).first()
        if entitlement and as_utc(entitlement.source_event_timestamp) >= as_utc(
            source_event_timestamp
        ):
            return entitlement, False

        if not entitlement:
            entitlement = cls(subject=subject, client_id=client_id)
        entitlement.plan = plan
        entitlement.billing_status = billing_status
        entitlement.payment_event_id = payment_event_id
        entitlement.source_event_timestamp = source_event_timestamp
        entitlement.updated_at = datetime.now(pytz.utc)
        entitlement.save()
        return entitlement, True
