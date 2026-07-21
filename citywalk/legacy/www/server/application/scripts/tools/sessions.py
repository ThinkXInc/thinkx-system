#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# tools/sessions.py
#
# Overrided class from libcommon.session.
#

import redis
from redis import StrictRedis, Redis
from libcommon.session import Session
from general.config import Config

class UserSession(Session):

    pool = redis.ConnectionPool(
        host=Config.REDIS_HOST_SESSION,
        port=Config.REDIS_PORT_SESSION,
        db=Config.REDIS_DB_NUMBER_SESSION_USERS
    )
    __redis = StrictRedis(connection_pool=pool)


class OrganizationMemberSession(Session):

    pool = redis.ConnectionPool(
        host=Config.REDIS_HOST_SESSION,
        port=Config.REDIS_PORT_SESSION,
        db=Config.REDIS_DB_NUMBER_SESSION_ORGANIZATIONS
    )
    __redis = StrictRedis(connection_pool=pool)