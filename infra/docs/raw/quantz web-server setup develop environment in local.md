# quantz web-server setup develop environment in local

_created: 20240519T031049Z / updated: 20241008T040426Z_

```
git clone git@github.com:ThinkXInc/quantz.git
cd quantz
git submodule sync
git submodule update --init --recursive
```

or

```
cd web-server
git submodule sync -- libcommon
git submodule update --init -- libcommon
```

```
cd web-server
python3.9 -m venv venv
pip install -r requirements-local.txt
```

```
vim /path/to/quantz/.env
# 以下を書いて保存
```

```
ENV=local

# App
FLASK_APP_SECRET_KEY = <REDACTED>
PASSWORD_ENCRYPT_KEY=<REDACTED>

# Redis Cache
REDIS_CACHE_HOST=localhost
REDIS_CACHE_PORT=6380
REDIS_CACHE_LOGLEVEL=debug
REDIS_CACHE_EXPIRATION_TIME_SEC=180
#REDIS_CACHE_PASSWORD=<REDACTED>

# Redis Session
REDIS_SESSION_HOST=localhost
REDIS_SESSION_PORT=6379
REDIS_SESSION_DB_NUMBER=1
REDIS_SESSION_LOGLEVEL=debug
REDIS_SESSION_EXPIRATION_TIME_SEC=90

# Redis AccessDB
REDIS_ACCESS_HOST=localhost
REDIS_ACCESS_PORT=6376
REDIS_ACCESS_DB_NUMBER=0

# Redis Chatdata
REDIS_CHATDATA_HOST=localhost
REDIS_CHATDATA_PORT=6378
REDIS_CHATDATA_DB_NUMBER=0
REDIS_CHATDATA_LOGLEVEL=debug
REDIS_CHATDATA_EXPIRATION_TIME_SEC=604800
REDIS_CHATDATA_QUEUE_NAME=chatdata_queue

# MongoDB
MONGO_DB_URI=localhost
MONGO_PASS=pass

# VectorDB
VECTORDB_ENCODER_CHECKPOINT=sentence-transformers/all-MiniLM-L6-v2
VECTORDB_EMBEDDING_DIM=384
#VECTORDB_ENCODER_CHECKPOINT=sentence-transformers/all-mpnet-base-v2
#VECTORDB_EMBEDDING_DIM=768
VECTORDB_HOST=localhost
VECTORDB_PORT=6333

# AWS
AWS_ACCESS_KEY_ID=<REDACTED>
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=ap-northeast-1

# Stripe
STRIPE_SECRET_KEY=
```

```
cd /path/to/web-server
cd views
npm install
```

simplicity/dist/simplicity.js, simplicity/dist/simplicity_default.css を手動でセット

```
cp -r simplicity /path/to/web-server/views/js/
```

*本来views/src/simplicityをビルドするスクリプトを動かしコピーする処理がpackage.jsonにありこれを動かしたいがまだできていない<-TODO

Run web-server and js/less compiler

```
cd /path/to/quantz/local
screen -c .screenrc
```
