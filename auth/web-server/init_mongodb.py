#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# init_mongodb.py — MongoDB 接続 (main.py の import 時に一度だけ実行される)
#
# quantz-web の同名ファイルと同じ役割。ただし quantz と違い try/except で握り潰さない
# (fail loudly — 接続設定の誤りは起動時に大声で落とす)。
# テストからは、この import より前に mongoengine.connect を mongomock へ
# monkeypatch する (libcommon 計画 Q-1 と同じ機構)。

from mongoengine import connect

# Logger
from libcommon.logger import Logger
from libcommon.color import *
logger = Logger()
logger.setLevel(logger.DEBUG)

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'MONGODB_DB_NAME',
    'MONGODB_HOST',
    'MONGODB_PORT',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

connect(
    db=Config.MONGODB_DB_NAME,
    host=Config.MONGODB_HOST,
    port=Config.MONGODB_PORT,
)
logger.info(green(f'MongoDB connected: {Config.MONGODB_DB_NAME}'))
