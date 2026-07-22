# auth/web-server/oidc/signin.py
#
# Login CSRF state for signin requests that resume an OIDC authorization.

import hmac
import secrets
from urllib.parse import urlsplit

from flask import request, session

from config import Config


CSRF_SESSION_KEY = 'oidc_signin_csrf_token'
REQUEST_HANDLE_SESSION_KEY = 'oidc_signin_request_handle'


def expected_origin():
    public_url = urlsplit(Config.AUTH_PUBLIC_BASE_URL)
    return f'{public_url.scheme}://{public_url.netloc}'


def issue_signin_csrf_token(request_handle):
    csrf_token = secrets.token_urlsafe(32)
    session[CSRF_SESSION_KEY] = csrf_token
    session[REQUEST_HANDLE_SESSION_KEY] = request_handle
    return csrf_token


def valid_signin_csrf(payload):
    request_handle = payload.get('request_handle')
    csrf_token = payload.get('csrf_token')
    saved_handle = session.get(REQUEST_HANDLE_SESSION_KEY)
    saved_token = session.get(CSRF_SESSION_KEY)
    if not all((request_handle, csrf_token, saved_handle, saved_token)):
        return False
    if not hmac.compare_digest(request_handle, saved_handle):
        return False
    if not hmac.compare_digest(csrf_token, saved_token):
        return False
    if request.headers.get('Origin') != expected_origin():
        return False
    fetch_site = request.headers.get('Sec-Fetch-Site')
    return fetch_site in (None, 'same-origin')


def clear_signin_csrf():
    session.pop(CSRF_SESSION_KEY, None)
    session.pop(REQUEST_HANDLE_SESSION_KEY, None)
