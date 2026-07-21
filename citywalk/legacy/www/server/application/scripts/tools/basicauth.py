#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# basicauth.py
#

from functools import wraps
from flask import request, Response
from general.config import Config


def check_auth(username, password):
    return username == Config.BASIC_AUTH_NAME\
        and password == Config.BASIC_AUTH_PASSWORD


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
