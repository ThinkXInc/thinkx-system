#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/data/user.py (auth)
#
# 全サービス共通アカウントの User。quantz-web の User から「アカウントの本質」だけを抽出。
# サービス固有の値 (free_call 等) は持たない — それは各サイトが user_id をキーに自分の DB で持つ。
# auth の User が持つのは: 身元 (email/password/google_id) + 表示 (name/picture_url/lang)
# + 課金 (services / stripe_customer_id) のみ。
#
# services の内部表現 (protocol.py が build_services でワイヤ形式へ変換する):
#   { service_id: {'plan': 'free'|'pro'..., 'stripe_subscription_status': Stripeの生値|None} }
# エントリはそのサービスへの初回ログイン成立時 (authorize) に ensure_service で作られ、
# Stripe webhook が課金状態を更新する。

from datetime import datetime
import pytz

from mongoengine import (
    StringField, EmailField, BooleanField, DateTimeField, DictField,
    DoesNotExist, MultipleObjectsReturned, NotUniqueError,
)

from libcommon.mongomodel import MongoModel
from libcommon.cipher import Cipher

# Logger
from libcommon.logger import Logger
from libcommon.color import *
logger = Logger()
logger.setLevel(logger.DEBUG)

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'ENV',
    'DEFAULT_LANG',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)


class UserSaveError(Exception):
    pass

class UserAlreadyExistsError(Exception):
    pass

class UserNotFoundError(Exception):
    pass

class UserQueryError(Exception):
    pass

class UnauthorizedAccessError(Exception):
    # L-1 (v2.0.0) 追随後: libcommon はこの例外を import しない。auth が app_session.py で
    # make_session_helper(on_no_session=UnauthorizedAccessError) として注入する。
    # 例外の所有はホスト側 (auth) に留まり、レイヤ逆転は解消された。
    pass


class User(MongoModel):
    meta = {'collection': 'users'}

    # --- 身元 ---
    email = EmailField(required=True, unique=True)
    email_verified = BooleanField(default=False)
    password = StringField()            # Cipher でハッシュ済み。Google ログインのみなら None
    google_id = StringField()           # Google OAuth の sub (境界の外の名前は境界で読む)

    # --- 表示 (UserInfo の材料) ---
    name = StringField()
    picture_url = StringField()
    lang = StringField(default=Config.DEFAULT_LANG)

    # --- 課金 (真実は Stripe。ここはそのミラー。webhook で更新) ---
    services = DictField(default=dict)
    stripe_customer_id = StringField()  # Stripe 顧客はアカウントに一つ。subscription はサービス単位

    # --- 記録 ---
    created_at = DateTimeField(default=lambda: datetime.now(pytz.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(pytz.utc))

    # ----------------------------------------------------------
    @classmethod
    def create_new(cls, email, password, lang=None, **kwargs):
        """メール+パスワードで新規作成。パスワードは Cipher でハッシュして保存。"""
        try:
            user = cls(
                email=email,
                password=Cipher.encrypt(password),
                lang=lang or Config.DEFAULT_LANG,
                **kwargs,
            )
            user.save()
            logger.info(green(f'New auth user created: {email}'))
            return user
        except NotUniqueError:
            logger.info(yellow(f'User already exists: {email}'))
            raise UserAlreadyExistsError(email)
        except Exception as e:
            logger.error(red(f'Failed to save user: {e}'))
            raise UserSaveError(str(e))

    @classmethod
    def create_new_google_oauth(cls, email, google_id, lang=None, **kwargs):
        """Google OAuth で新規作成。email_verified は Google 側で検証済みなので True。"""
        try:
            user = cls(
                email=email,
                google_id=google_id,
                email_verified=True,
                lang=lang or Config.DEFAULT_LANG,
                **kwargs,
            )
            user.save()
            logger.info(green(f'New auth user created via Google OAuth: {email}'))
            return user
        except NotUniqueError:
            raise UserAlreadyExistsError(email)

    @classmethod
    def find_user_by_email(cls, email):
        try:
            return cls.objects.get(email=email)
        except DoesNotExist:
            raise UserNotFoundError(email)
        except MultipleObjectsReturned as e:
            logger.error(red(f'Multiple users for email {email}: {e}'))
            raise UserQueryError(str(e))

    @classmethod
    def find_user_by_id(cls, user_id):
        try:
            return cls.objects.get(id=user_id)
        except DoesNotExist:
            raise UserNotFoundError(user_id)

    def check_password(self, raw_password):
        if not self.password:
            return False
        return Cipher.compare(raw_password, self.password)

    def ensure_service(self, service_id):
        """サービスの利用エントリを保証する。初回ログイン成立時 (authorize) に呼ぶ。

        既にあれば何もしない。無ければ plan='free' で作る (PROTOCOL.md §3 の生成規則)。
        """
        if not service_id:
            return
        services = dict(self.services or {})
        if service_id in services:
            return
        services[service_id] = {'plan': 'free', 'stripe_subscription_status': None}
        self.services = services
        self.updated_at = datetime.now(pytz.utc)
        self.save()
        logger.info(cyan(f'service entry created: user={self.id} service_id={service_id}'))
