#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
from os.path import dirname, abspath, join
from dotenv import load_dotenv

class EnvironmentNotSpecified(Exception):
    pass


class Config:
    # www/server/application/scripts
    SRC_ROOT = dirname(dirname(abspath(__file__)))  
    # www/server/application/messages
    MESSAGES_ROOT = join(dirname(SRC_ROOT), 'messages')
    # www
    PRJ_ROOT = dirname(dirname(dirname(SRC_ROOT)))
    # www/server/application/scripts/data
    DATA_DIR = join(SRC_ROOT, 'data')

    ANIMAL_NAME_MECAB_DIC_PATH = join(DATA_DIR, 'animal/animal_name.dic')
    # TODO: ansible によるinstall 場所に変更する
    MECAB_SYSTEM_DIC_PATH = '/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd'

    DOTENV_PATH = join(PRJ_ROOT, '.env')

    if os.path.exists(DOTENV_PATH):
        load_dotenv(DOTENV_PATH)
    else:
        print('[WARNING] no .env file exists in {}'.format(DOTENV_PATH))

    env = os.environ.get("ENV")
    print(DOTENV_PATH)
    print(env)
    if env == "production":
        MONGO_DB_URI = os.environ.get("PRODUCTION_MONGO_DB_URI")
        MONGO_PASS = os.environ.get("PRODUCTION_MONGO_PASS")
        AWS_PROFILE_NAME = 'citywalk-api'
        S3_BUCKET_NAME_MONGO_DUMP = "citywalk-mongo-dump"
        S3_BUCKET_NAME_CONTENTS = 'citywalk-contents'
        REDIS_HOST_SESSION = os.environ.get("REDIS_HOST_SESSION")
        REDIS_PORT_SESSION = os.environ.get("REDIS_PORT_SESSION")
        REDIS_DB_NUMBER_SESSION_USERS = 0
        REDIS_DB_NUMBER_SESSION_ORGANIZATIONS = 1
        REDIS_SESSION_EXPIRATION_PERIOD = 90
        BATCH_LOG_DIR = '/var/log/citywalk'
        BATCH_LOG_FILE_PATH = '{}/batch.log'.format(BATCH_LOG_DIR)
        POS_DIR = '/var/POS'
        ITEM_DIR = '/var/PRD'
        MAIL_SENDER = 'CITYWALK <info@citywalk.app>'
        SES_AWS_REGION = 'us-west-2'
        HOST_URL = "https://citywalk.app"
        LOG_LEVEL = logging.INFO
        LOG_FILEPATH = f'/var/log/citywalk.log'
        FACEBOOK_APP_ID = os.environ.get("FACEBOOK_APP_ID")
        FACEBOOK_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET")
    elif env == "staging":
        MONGO_DB_URI = os.environ.get("STAGING_MONGO_DB_URI")
        MONGO_PASS = os.environ.get("STAGING_MONGO_PASS")
        AWS_PROFILE_NAME = 'citywalk-api-develop'
        S3_BUCKET_NAME_MONGO_DUMP = "citywalk-mongodump-develop"
        S3_BUCKET_NAME_CONTENTS = 'citywalk-contents-develop'
        REDIS_HOST_SESSION = os.environ.get("REDIS_HOST_SESSION")
        REDIS_PORT_SESSION = os.environ.get("REDIS_PORT_SESSION")
        REDIS_DB_NUMBER_SESSION_USERS = 0
        REDIS_DB_NUMBER_SESSION_ORGANIZATIONS = 1
        REDIS_SESSION_EXPIRATION_PERIOD = 7
        BATCH_LOG_DIR = '/var/log/citywalk'
        BATCH_LOG_FILE_PATH = '{}/batch.log'.format(BATCH_LOG_DIR)
        POS_DIR = '/var/POS'
        ITEM_DIR = '/var/PRD'
        MAIL_SENDER = 'CITYWALK <info@citywalk.app>'
        SES_AWS_REGION = 'us-west-2'
        HOST_URL = "https://citywalk.app"
        LOG_LEVEL = logging.DEBUG
        LOG_FILEPATH = f'/var/log/citywalk.log'
        FACEBOOK_APP_ID = os.environ.get("FACEBOOK_APP_ID")
        FACEBOOK_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET")
    elif env == "local":
        MONGO_DB_URI = 'mongodb://localhost:27017/citywalk'
        MONGO_DB_URI_TEST = 'mongodb://localhost:27017/citywalk-test'
        MONGO_PASS = None
        MONGO_DB_TEST_DUMPFILES_ROOT = join(
            DATA_DIR, 'unittests/dumps/citywalk-test')
        AWS_PROFILE_NAME = 'citywalk-api-develop'
        S3_BUCKET_NAME_MONGO_DUMP = "citywalk-mongodump-develop"
        S3_BUCKET_NAME_CONTENTS = 'citywalk-contents-develop'
        REDIS_HOST_SESSION = 'localhost'
        REDIS_PORT_SESSION = '6379'
        REDIS_DB_NUMBER_SESSION_USERS = 0
        REDIS_DB_NUMBER_SESSION_ORGANIZATIONS = 1
        REDIS_SESSION_EXPIRATION_PERIOD = 1
        BATCH_LOG_DIR = join(PRJ_ROOT, 'logs')
        BATCH_LOG_FILE_PATH = '{}/batch.log'.format(BATCH_LOG_DIR)
        POS_DIR = '/var/POS'
        ITEM_DIR = '/var/PRD'
        TEST_IMAGE_FILE_PATH = join(DATA_DIR, 'unittests/images/image.jpg')
        SES_AWS_REGION = 'us-west-2'
        MAIL_SENDER = 'CITYWALK <info@citywalk.app>'
        REPLY_TO_ADDRESSES = ['support@citywalk.app']
        HOST_URL = "http://citywalkservers.localhost:8000"
        LOG_LEVEL = logging.DEBUG
        LOG_FILEPATH = f'{PRJ_ROOT}/citywalk.log'
        FACEBOOK_APP_ID = None
        FACEBOOK_APP_SECRET = None
    elif env == "test":
        MONGO_DB_URI = 'mongodb://localhost:27017/citywalk-test'
        MONGO_DB_URI_TEST = 'mongodb://localhost:27017/citywalk-test'
        MONGO_DB_TEST_DUMPFILES_ROOT = join(
            DATA_DIR, 'unittests/dumps/citywalk-test')
        S3_BUCKET_NAME_MONGO_DUMP = "citywalk-mongodump-test"
        S3_BUCKET_NAME_CONTENTS = 'citywalk-contents-test'
        REDIS_HOST_SESSION = 'localhost'
        REDIS_PORT_SESSION = '6379'
        REDIS_DB_NUMBER_SESSION_USERS = 2
        REDIS_DB_NUMBER_SESSION_ORGANIZATIONS = 3
        REDIS_SESSION_EXPIRATION_PERIOD = 1
        BATCH_LOG_DIR = join(PRJ_ROOT, 'logs')
        BATCH_LOG_FILE_PATH = '{}/batch.log'.format(BATCH_LOG_DIR)
        POS_DIR = join(DATA_DIR, 'unittests/POS')
        ITEM_DIR = join(DATA_DIR, 'item_master.csv')
        TEST_IMAGE_FILE_PATH = join(DATA_DIR, 'unittests/images/image.jpg')
        SES_AWS_REGION = 'us-west-2'
        MAIL_SENDER = 'CITYWALK <info@citywalk.app>'
        REPLY_TO_ADDRESSES = ['support@citywalk.app']
        HOST_URL = "http://citywalkservers.localhost:8000"
        LOG_LEVEL = logging.DEBUG
        LOG_FILEPATH = f'{PRJ_ROOT}/citywalk.log'
        FACEBOOK_APP_ID = None
        FACEBOOK_APP_SECRET = None
    else:
        print('no env specified')
        raise EnvironmentNotSpecified

    # default language
    DEFAULT_LANGUAGE = 'ja'

    # password encryption key
    ENCRYPT_KEY = os.environ.get("ENCRYPT_KEY")
    if not ENCRYPT_KEY:
        assert False, '!!!! ENCRYPT_KEY in .env is necessary.'

    # logger format
    LOG_FORMAT = "%(asctime)-15s [%(levelname)s] %(message)s"

    # session
    REDIS_DB_NUMBER_SESSION = None  # not in use

    # mongodb
    MONGO_DB_NAME = "citywalk" \
        if env != "emrtest" else "citywalk-test"
    MONGO_DB_NAME_TEST = "citywalk-test"

    MONGO_DB_CONNECT_TIMEOUT_MS = 3000
    MONGO_DB_SERVER_SELECTION_TIMEOUT_MS = 3000
    MONGO_DB_SOCKET_TIMEOUT_MS = 300000
    MONGO_DB_SOCKET_KEEP_ALIVE = True
    MONGO_DB_MAX_IDLE_TIME_MS = 40000
    MONGO_DB_MAX_POOL_SIZE = 100
    MONGO_DB_MIN_POOL_SIZE = 0
    MONGO_DB_WAIT_QUEUE_MULTIPLE = 12
    MONGO_DB_WAIT_QUEUE_TIMEOUT_MS = 100
    MONGO_BACKUP_COLLECTIONS = [
        {
            "collection_name": "aggregate_results",
            "package_name": "models.aggregate_results",
            "class_name": "AggregateResults",
        },
        {
            "collection_name": "recommend",
            "package_name": "models.recommend",
            "class_name": "Recommend",
        },
        {
            "collection_name": "fish_recommend",
            "package_name": "models.fish_recommend",
            "class_name": "FishRecommend",
        },
        {
            "collection_name": "history",
            "package_name": "models.history",
            "class_name": "History",
        },
    ]
    MONGO_BACKUP_BEFORE_DAYS = 365

    # Slack alert
    ALERT_SLACK_HOOK_URLS = [
        os.environ.get("ALERT_SLACK_HOOK_URL_6TH"),
        os.environ.get("ALERT_SLACK_HOOK_URL_SIRUTASU")
    ]
    BATCH_SLACK_HOOK_URLS = [
        os.environ.get("BATCH_SLACK_HOOK_URL_6TH"),
        os.environ.get("BATCH_SLACK_HOOK_URL_SIRUTASU")
    ]

    # flask secret key
    FLASK_TEST_SECRET_KEY = 'test'
    FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

    # basic auth
    BASIC_AUTH_USER = 'beta'
    BASIC_AUTH_PASS = 'cryptoxanthin'

    # password reset code
    PASSWORD_REMINDER_RESET_CODE_EXPIRATION_DAY = 1

    # signup verification code
    SIGNUP_VERIFICATION_CODE_EXPIRATION_HOUR = 48

    # change email verify code
    CHANGE_EMAIL_VERIFY_CODE_EXPIRATION_DAY = 1