# auth/web-server/models/data/user.py
#
# Central auth identity model. Public OIDC identity is subject_id, not MongoDB ObjectId.

from datetime import datetime
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from mongoengine import (
    DateTimeField,
    DoesNotExist,
    EmailField,
    EmbeddedDocument,
    EmbeddedDocumentListField,
    IntField,
    ListField,
    MultipleObjectsReturned,
    NotUniqueError,
    Q,
    StringField,
)
import pytz

from config import Config, check_config
from libcommon.color import green, red, yellow
from libcommon.logger import Logger
from libcommon.mongomodel import MongoModel


REQUIRED_KEYS_IN_CONFIG = ['ENV', 'DEFAULT_LANG']
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

logger = Logger()
logger.setLevel(logger.DEBUG)
password_hasher = PasswordHasher()


def create_random_subject_id():
    return secrets.token_urlsafe(32)


class UserSaveError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserQueryError(Exception):
    pass


class UnauthorizedAccessError(Exception):
    pass


class VerifiedEmail(EmbeddedDocument):
    email = EmailField(required=True)
    method = StringField(required=True)
    verified_at = DateTimeField(required=True)


class VerifiedPhoneNumber(EmbeddedDocument):
    phone_number = StringField(required=True)
    method = StringField(required=True)
    verified_at = DateTimeField(required=True)


class User(MongoModel):
    meta = {
        'collection': 'users',
        'indexes': [{
            'fields': ['email_identity_keys'],
            'unique': True,
            'partialFilterExpression': {
                'email_identity_keys.0': {'$exists': True},
            },
        }],
    }

    email = EmailField(unique=True, sparse=True)
    suspended_email = EmailField(unique=True, sparse=True)
    # MongoDB cannot make two separate fields mutually unique. This internal
    # multikey projection gives email and suspended_email one DB-level boundary.
    email_identity_keys = ListField(EmailField(), default=list)
    verified_emails = EmbeddedDocumentListField(VerifiedEmail, default=list)
    verified_phone_numbers = EmbeddedDocumentListField(
        VerifiedPhoneNumber, default=list
    )
    password = StringField()
    google_id = StringField(unique=True, sparse=True)
    subject_id = StringField(required=True, unique=True, default=create_random_subject_id)

    name = StringField()
    picture_url = StringField()
    lang = StringField(default=Config.DEFAULT_LANG)

    auth_generation = IntField(default=0)
    last_auth_time = DateTimeField()
    status = StringField(default='active', choices=('active', 'suspended'))
    created_at = DateTimeField(default=lambda: datetime.now(pytz.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(pytz.utc))

    def clean(self):
        self.email_identity_keys = list(dict.fromkeys(
            value for value in (self.email, self.suspended_email) if value
        ))

    @classmethod
    def _users_with_email(cls, email):
        return cls.objects(Q(email=email) | Q(suspended_email=email))

    @classmethod
    def _assert_email_available(cls, email):
        if cls._users_with_email(email).first() is not None:
            raise UserAlreadyExistsError(email)

    @classmethod
    def create_new(cls, email, password, lang=None, **kwargs):
        try:
            cls._assert_email_available(email)
            user = cls(
                suspended_email=email,
                password=password_hasher.hash(password),
                lang=lang or Config.DEFAULT_LANG,
                **kwargs,
            ).save()
            logger.info(green(f'New auth user created: {email}'))
            return user
        except UserAlreadyExistsError:
            raise
        except NotUniqueError:
            logger.info(yellow(f'User already exists: {email}'))
            raise UserAlreadyExistsError(email)
        except Exception as error:
            logger.error(red(f'Failed to save user: {error}'))
            raise UserSaveError(str(error)) from error

    @classmethod
    def create_new_google_oauth(cls, email, google_id, lang=None, **kwargs):
        try:
            cls._assert_email_available(email)
            verified_email = {
                'email': email,
                'method': 'google',
                'verified_at': datetime.now(pytz.utc),
            }
            return cls(
                email=email,
                verified_emails=[verified_email],
                google_id=google_id,
                lang=lang or Config.DEFAULT_LANG,
                **kwargs,
            ).save()
        except UserAlreadyExistsError:
            raise
        except NotUniqueError as error:
            raise UserAlreadyExistsError(email) from error

    @classmethod
    def find_user_by_email(cls, email):
        try:
            return cls._users_with_email(email).get()
        except DoesNotExist as error:
            raise UserNotFoundError(email) from error
        except MultipleObjectsReturned as error:
            logger.error(red(f'Multiple users for email {email}: {error}'))
            raise UserQueryError(str(error)) from error

    @classmethod
    def find_user_by_id(cls, user_id):
        try:
            return cls.objects.get(id=user_id)
        except DoesNotExist as error:
            raise UserNotFoundError(user_id) from error

    @classmethod
    def find_user_by_google_id(cls, google_id):
        try:
            return cls.objects.get(google_id=google_id)
        except DoesNotExist as error:
            raise UserNotFoundError(google_id) from error

    def apply_google_identity(self, email, google_id):
        if self.google_id and self.google_id != google_id:
            raise UnauthorizedAccessError(google_id)
        conflicting_user = self._users_with_email(email).filter(
            id__ne=self.id
        ).first()
        if conflicting_user is not None:
            raise UserAlreadyExistsError(email)

        if not self.is_email_verified(email):
            self.verified_emails.append(VerifiedEmail(
                email=email,
                method='google',
                verified_at=datetime.now(pytz.utc),
            ))
        self.email = email
        if self.suspended_email == email:
            self.suspended_email = None
        self.google_id = google_id
        self.updated_at = datetime.now(pytz.utc)
        try:
            self.save()
        except NotUniqueError as error:
            raise UserAlreadyExistsError(email) from error
        return self

    def check_password(self, raw_password):
        if not self.password:
            return False
        try:
            return password_hasher.verify(self.password, raw_password)
        except (InvalidHashError, VerifyMismatchError):
            return False

    def is_active(self):
        return self.status == 'active'

    def subject(self):
        return self.subject_id

    def is_primary_email_verified(self):
        return bool(self.email) and self.is_email_verified(self.email)

    def is_email_verified(self, email):
        return email in [entry.email for entry in self.verified_emails]

    def ensure_service(self, service_id):
        if not service_id:
            return
        from models.data.connected_service import ConnectedService

        ConnectedService.connect(self.subject_id, service_id)
