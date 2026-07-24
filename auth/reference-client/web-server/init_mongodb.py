# auth/reference-client/web-server/init_mongodb.py
#
# MongoDB connection initialization for reference-client durable identity data.

from mongoengine import connect

from config import Config, check_config


check_config(Config, ('MONGODB_DB_NAME', 'MONGODB_HOST', 'MONGODB_PORT'))
connect(
    db=Config.MONGODB_DB_NAME,
    host=Config.MONGODB_HOST,
    port=Config.MONGODB_PORT,
)
