# auth/web-server/config.py
# 実際の config.py は各環境で作成 (既存アプリと同じ流儀)。secret はコミットしない。

import os

class Config:
    ENV = os.environ.get('ENV', 'development')
    AUTH_PUBLIC_BASE_URL = os.environ.get(
        'AUTH_PUBLIC_BASE_URL', 'http://127.0.0.1:8020'
    )
    OIDC_ID_TOKEN_TTL_SEC = 600
    SIGNING_KEY_OVERLAP_SECONDS = 3600
    OIDC_AUTHORIZATION_REQUEST_TTL_SEC = 600
    SIGNUP_CHALLENGE_TTL_SEC = 3600
    PASSWORD_RESET_EXPIRATION_SECONDS = 3600
    AUTH_SMTP_HOST = os.environ.get('AUTH_SMTP_HOST')
    AUTH_SMTP_PORT = int(os.environ.get('AUTH_SMTP_PORT', '587'))
    AUTH_SMTP_STARTTLS = os.environ.get('AUTH_SMTP_STARTTLS', '1') == '1'
    AUTH_SMTP_USERNAME = os.environ.get('AUTH_SMTP_USERNAME')
    AUTH_SMTP_PASSWORD = os.environ.get('AUTH_SMTP_PASSWORD')
    AUTH_EMAIL_SENDER = os.environ.get('AUTH_EMAIL_SENDER', 'account@thinkx.jp')
    PAYMENT_PROJECTION_WEBHOOK_SECRET = os.environ.get(
        'PAYMENT_PROJECTION_WEBHOOK_SECRET'
    ) or (
        'development-payment-projection-secret'
        if ENV in ('development', 'test') else None
    )

    # --- 言語 (libcommon/web/flask_helpers.py の要求キー) ---
    DEFAULT_LANG = 'en'
    AVAILABLE_LANGS = ['en', 'ja']
    LANG_NAME_MAP = {'en': 'English', 'ja': '日本語'}

    # --- mongodb (init_mongodb.py の要求キー) ---
    MONGODB_DB_NAME = 'thinkx_auth'
    MONGODB_HOST = '127.0.0.1'
    MONGODB_PORT = 27017

    # --- session (libcommon/web/session.py の要求キー) ---
    SESSION_COOKIE_NAME = 'thinkx_auth_session'   # サイト固有名。サイトと共有しない
    REDIS_SESSION_HOST = '127.0.0.1'
    REDIS_SESSION_PORT = 6379
    REDIS_SESSION_DB_NUMBER = 3                   # 各サイトのセッション DB と衝突しない番号
    REDIS_SESSION_EXPIRATION_TIME_SEC = 60 * 60 * 24 * 30

    # --- sso ---
    SSO_REDIS_DB_NUMBER = 4                       # auth_code / access_token 置き場
    SSO_CODE_TTL_SEC = 60                         # 認可コードは 60 秒・一回限り
    SSO_ACCESS_TOKEN_TTL_SEC = 3600

    # サービス (サイト) の静的登録。サービス追加 = ここに1エントリ足して deploy。
    # redirect_uri は完全一致で検証される (PROTOCOL.md §2 手順3)。
    # キー名は service_secret / redirect_uris / logout_uris のみ。別名は作らない。
    SSO_SERVICES = {
        'quantz': {
            'service_secret': 'CHANGE_ME_quantz_secret',
            'redirect_uris': [
                'https://quantz.example.com/auth/callback',
                'http://127.0.0.1:8000/auth/callback',   # local
            ],
            'logout_uris': [
                'https://quantz.example.com/',
            ],
        },
        'podcast': {
            'service_secret': 'CHANGE_ME_podcast_secret',
            'redirect_uris': ['https://podcast.example.com/auth/callback'],
            'logout_uris': ['https://podcast.example.com/'],
        },
    }

    # --- google oauth (libcommon/web/google_oauth_helper.py の要求キー) ---
    GOOGLE_OAUTH_CLIENT_ID = 'CHANGE_ME.apps.googleusercontent.com'

    # --- basic auth (libcommon/web/flask_helpers.py の要求キー) ---
    BASIC_AUTH_USERNAME = 'admin'
    BASIC_AUTH_PASSWORD = 'CHANGE_ME'

    # --- cipher (libcommon/cipher.py の要求キー。models/data/user.py 経由で import される) ---
    # ローカル/テスト用ダミー。パスワード暗号化の AES 鍵。本番は .env から注入する。
    PASSWORD_ENCRYPT_KEY = 'CHANGE_ME_dummy_local_encrypt_key'


def check_config(config, required_keys):
    for key in required_keys:
        if not hasattr(config, key):
            raise RuntimeError(f'Config missing required key: {key}')
