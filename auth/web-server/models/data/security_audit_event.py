# auth/web-server/models/data/security_audit_event.py
#
# Append-only security events. Secrets and verification codes never belong here.

from datetime import datetime

from mongoengine import DateTimeField, StringField
import pytz

from libcommon.mongomodel import MongoModel


class SecurityAuditEvent(MongoModel):
    meta = {
        'collection': 'security_audit_events',
        'indexes': ['subject', 'occurred_at'],
    }

    event_type = StringField(required=True)
    subject = StringField(required=True)
    occurred_at = DateTimeField(default=lambda: datetime.now(pytz.utc))

    @classmethod
    def record(cls, *, event_type, subject):
        return cls(event_type=event_type, subject=subject).save()

    def save(self, *args, **kwargs):
        if self.pk and not self._created:
            raise RuntimeError('SecurityAuditEvent records are append-only')
        return super().save(*args, **kwargs)
