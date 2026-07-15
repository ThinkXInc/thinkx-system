import sys
import os
import json
from os.path import abspath, join
from urllib.parse import quote
import atexit
from jinja2 import TemplateNotFound
from flask import abort, Flask, render_template, request, g, jsonify, url_for, redirect

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'DEFAULT_LANG',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

# Locale
from libcommon.language import Language
from libcommon.locale import Locale, COMMON_LOCALES_FILE_PATHS

# Set logger
from libcommon.logger import Logger
logger = Logger('main.py')
logger.setLevel(logger.DEBUG)
from libcommon.color import *
from libcommon.validator import Validator, ValidationType

# Web API tools
from libcommon.web.validation_errors import RequiredFieldsNotSatisfiedFormat
from libcommon.web.http_errors import InvalidContentTypeAPIErrorFormat, \
    UnexpectedAPIErrorFormat, ForbiddenAPIErrorFormat, ResourceNotFoundAPIErrorFormat, \
    BadRequestAPIErrorFormat, UnauthorizedAPIErrorFormat, RateLimitExceededAPIErrorFormat
from libcommon.web.http_successes import OKAPISuccessFormat, CreatedAPISuccessFormat, \
    AcceptedAPISuccessFormat
from flask_helper import language_wrapper, handle_error

COMMON_LOCALES_ROOT = join(abspath(__file__), 'libcommon/locales')
LOCALES_ROOT = Config.LOCALES_ROOT
ERROR_PAGES_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/error_pages.json'
METADATA_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/page_metadata.json'
#HEADER_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/header.json'
locale = Locale([
    ERROR_PAGES_LOCALE_FILE_PATH,
    METADATA_LOCALE_FILE_PATH,
    #HEADER_LOCALE_FILE_PATH,
])

# Email
from mails.send_mail import (
    send_inquiry_confirm_email,
    MailSendError
)

# Initialize flask app
from init_flask_app import app

DEFAULT_LANG = Config.DEFAULT_LANG

## basic handlers
#@app.route('/')
#@app.route('/<lang>/')
#@language_wrapper
#def top_handler(lang, lang_name):
#    logger.info(magenta(f'=> / [GET]'))
#    locale.add_locale_file(TOP_PAGE_LOCALE_FILE_PATH)
#    locale.add_locale_file(MESSAGE_LOCALE_FILE_PATH)
#    return render_template(
#        'index.html',
#        page_id='home',
#        lang=lang,
#        lang_name=lang_name,
#        locale_dict=locale.dict(),
#        metadata=locale.dict()["metadata_home"][lang]
#    )

@app.route('/')
@language_wrapper
def top_handler(lang, lang_name):
    return render_template(
        'index.html',
        page_id='home',
        lang=lang,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_home"][lang])


@app.errorhandler(400)
@language_wrapper
def bad_request(error, lang, lang_name):
    return handle_error(error, BadRequestAPIErrorFormat, lang)

@app.errorhandler(404)
@language_wrapper
def page_not_found(error, lang, lang_name):
    logger.error(red(f"404 Page Not Found: {request.url}"))
    return render_template(
        '/errors/404.html',
        message=locale.get("404", lang),
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_home"][lang]
        ), 404

@app.errorhandler(500)
@language_wrapper
def internal_server_error(error, lang, lang_name):
    return handle_error(error, UnexpectedAPIErrorFormat, lang)

@app.errorhandler(502)
@language_wrapper
def bad_gateway(error, lang, lang_name):
    return handle_error(error, RateLimitExceededAPIErrorFormat, lang)



app.secret_key = \
        '\xa0\x88^\x92\xb7\xe5:>:\xc5\xa7s$\xdf\xf8m\xe9|-R\xe8,\xba\x81'

if __name__ == '__main__':
    app.run(
            debug=True,
            secret_key='D0Ls/9 lO~a2Lh[,3!3',
            max_content_length=70000000)
