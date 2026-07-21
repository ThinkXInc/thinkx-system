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
    IntField,
    ListField,
    MultipleObjectsReturned,
    NotUniqueError,
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


class User(MongoModel):
    meta = {'collection': 'users'}

    email = EmailField(unique=True, sparse=True)
    suspended_email = EmailField(unique=True, sparse=True)
    verified_emails = ListField(default=list)
    verified_phone_numbers = ListField(default=list)
    password = StringField()
    google_id = StringField()
    subject_id = StringField(required=True, unique=True, default=create_random_subject_id)

    name = StringField()
    picture_url = StringField()
    lang = StringField(default=Config.DEFAULT_LANG)

    auth_generation = IntField(default=0)
    last_auth_time = DateTimeField()
    status = StringField(default='active', choices=('active', 'suspended'))
    created_at = DateTimeField(default=lambda: datetime.now(pytz.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(pytz.utc))

    @classmethod
    def create_new(cls, email, password, lang=None, **kwargs):
        try:
            user = cls(
                suspended_email=email,
                password=password_hasher.hash(password),
                lang=lang or Config.DEFAULT_LANG,
                **kwargs,
            ).save()
            logger.info(green(f'New auth user created: {email}'))
            return user
        except NotUniqueError:
            logger.info(yellow(f'User already exists: {email}'))
            raise UserAlreadyExistsError(email)
        except Exception as error:
            logger.error(red(f'Failed to save user: {error}'))
            raise UserSaveError(str(error)) from error

    @classmethod
    def create_new_google_oauth(cls, email, google_id, lang=None, **kwargs):
        try:
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
        except NotUniqueError as error:
            raise UserAlreadyExistsError(email) from error

    @classmethod
    def find_user_by_email(cls, email):
        try:
            return cls.objects.get(email=email)
        except DoesNotExist:
            try:
                return cls.objects.get(suspended_email=email)
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
        return email in [entry.get('email') for entry in self.verified_emails]

    @property
    def email_verified(self):
        return self.is_primary_email_verified()

    def ensure_service(self, service_id):
        if not service_id:
            return
        from models.data.connected_service import ConnectedService

        ConnectedService.connect(self.subject_id, service_id)
