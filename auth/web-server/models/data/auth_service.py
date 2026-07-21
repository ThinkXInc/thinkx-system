# auth/web-server/models/data/auth_service.py
#
# Static OAuth/OIDC client registration owned by auth.

import hashlib
import hmac

from mongoengine import BooleanField, ListField, StringField

from libcommon.mongomodel import MongoModel


def digest_client_secret(client_secret):
    return hashlib.sha256(client_secret.encode('utf-8')).hexdigest()


class AuthService(MongoModel):
    meta = {'collection': 'auth_services'}

    client_id = StringField(required=True, unique=True)
    secret_digest = StringField(required=True)
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
