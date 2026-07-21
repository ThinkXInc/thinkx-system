# auth/web-server/models/data/auth_service.py
#
# Static OAuth/OIDC client registration owned by auth.

import hashlib
import hmac
from datetime import datetime

from mongoengine import BooleanField, ListField, StringField
from pymongo import ReturnDocument
import pytz

from libcommon.mongomodel import MongoModel


def digest_client_secret(client_secret):
    return hashlib.sha256(client_secret.encode('utf-8')).hexdigest()


def validate_client_secret(client_secret):
    if not isinstance(client_secret, str) or len(client_secret.encode('utf-8')) < 32:
        raise ValueError('client_secret must contain at least 32 bytes')


class AuthService(MongoModel):
    meta = {'collection': 'auth_services'}

    client_id = StringField(required=True, unique=True)
    secret_digest = StringField(required=True, regex=r'^[0-9a-f]{64}$')
    redirect_uris = ListField(StringField(), required=True)
    allowed_scopes = ListField(StringField(), required=True)
    trusted_first_party = BooleanField(default=False)
    subject_type = StringField(default='public', choices=('public', 'pairwise'))
    id_token_signing_alg = StringField(default='RS256', choices=('RS256',))
    status = StringField(default='active', choices=('active', 'disabled'))
    revoke_url = StringField()
    revoke_webhook_secret = StringField()

    @classmethod
    def find(cls, client_id):
        return cls.objects(client_id=client_id).first()

    def verify_secret(self, client_secret):
        return hmac.compare_digest(self.secret_digest, digest_client_secret(client_secret))

    def valid_redirect(self, redirect_uri):
        return redirect_uri in self.redirect_uris

    @classmethod
    def provision(
        cls, *, client_id, client_secret, redirect_uris, allowed_scopes,
        trusted_first_party=False
    ):
        validate_client_secret(client_secret)
        secret_digest = digest_client_secret(client_secret)
        candidate = cls(
            client_id=client_id,
            secret_digest=secret_digest,
            redirect_uris=redirect_uris,
            allowed_scopes=allowed_scopes,
            trusted_first_party=trusted_first_party,
            subject_type='public',
            id_token_signing_alg='RS256',
            status='active',
        )
        candidate.validate()
        now = datetime.now(pytz.utc)
        raw = cls._get_collection().find_one_and_update(
            {'client_id': client_id},
            {
                '$set': {
                    'secret_digest': secret_digest,
                    'redirect_uris': list(redirect_uris),
                    'allowed_scopes': list(allowed_scopes),
                    'trusted_first_party': trusted_first_party,
                    'subject_type': 'public',
                    'id_token_signing_alg': 'RS256',
                    'status': 'active',
                    'updated': now,
                },
                '$setOnInsert': {'created': now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return cls._from_son(raw)
