# tests/conftest.py
#
# main / init_mongodb / libcommon.web.session を外部インフラ (実 MongoDB / 実 Redis) 無しで
# import・実行できるようにする。ここは main を import する「前」に実行される必要があるため、
# conftest のトップレベル (= pytest がテスト収集より前に読み込む場所) で差し替える。
#
#   - init_mongodb.py が import 時に mongoengine.connect(db, host, port) を呼ぶ
#     -> mongoengine.connect を functools.partial で mongomock.MongoClient を使う版に差し替える
#   - libcommon/web/session.py と sso.py が import 時に redis クライアントを構築する
#     -> redis.StrictRedis / redis.Redis / redis.ConnectionPool を fakeredis へ差し替える
#
# 実インフラへの推測的な API は増やさない。現行 vendored libcommon の import 時副作用に対して
# だけ最小限に介入する。

import functools
import os
import sys

import mongoengine
import mongomock
import redis
import fakeredis

# web-server をパスに載せる (main / config / sso / accounts / models はそこにある)。
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_SERVER = os.path.join(REPO_ROOT, 'web-server')
if WEB_SERVER not in sys.path:
    sys.path.insert(0, WEB_SERVER)

# cwd を web-server/locales へ移す。理由: sso.py / accounts.py が import 時に
# Locale('sso.json') / Locale('accounts.json') と「bare ファイル名」で呼び、
# vendored libcommon の locale.py は与えられたパスを cwd 相対でそのまま open するため。
# 実体は web-server/locales/*.json にある。quantz-web は Config.LOCALES_ROOT の絶対パスで
# Locale を呼ぶ規約 (auth はそこから逸脱)。これは findings に記録済みの app 側の逸脱であり、
# app ソースには手を入れず、テストは locale が解決できる cwd で import を検証する。
os.chdir(os.path.join(WEB_SERVER, 'locales'))

# --- MongoDB: mongoengine.connect を mongomock で行う (functools.partial 方式) ---
# 実の connect をキャプチャしてから、mongo_client_class を差し込んだ版へ束ね直す。
mongoengine.connect = functools.partial(
    mongoengine.connect, mongo_client_class=mongomock.MongoClient
)

# --- Redis: StrictRedis / Redis / ConnectionPool を fakeredis へ ---
# 単一の FakeServer を共有し、db 番号だけ尊重する (session=db3, sso=db4 が分離される)。
_fake_server = fakeredis.FakeServer()


def _fake_redis_client(*args, **kwargs):
    return fakeredis.FakeStrictRedis(server=_fake_server, db=kwargs.get('db', 0))


redis.StrictRedis = _fake_redis_client
redis.Redis = _fake_redis_client
redis.ConnectionPool = lambda *args, **kwargs: None
