from flask import request, g, abort, Response
from functools import wraps, partial

from libcommon.language import Language
from libcommon.locale import Locale
from libcommon.validator import Validator, ValidationType

# Set logger
from libcommon.logger import Logger
from libcommon.color import *

logger = Logger()
logger.setLevel(logger.DEBUG)

# config
from config import Config, check_config
REQUIRED_KEYS = [
    'DEFAULT_LANG',
]
check_config(Config, REQUIRED_KEYS)

DEFAULT_LANG = Config.DEFAULT_LANG
AVAILABLE_LANGS = Config.AVAILABLE_LANGS #['en', 'ja', 'zh', 'fr', 'ar', 'ru', 'es', 'ko', 'de']
LANG_NAME_MAP = Language.lang_label_map(only=AVAILABLE_LANGS)

def language_wrapper(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        logger.debug(f"Entering language_wrapper with URL path: {request.path}")
        # Step 1: Look at the URL
        path_parts = request.path.strip('/').split('/')

        # Step 2: Check if the 2nd part of the URL is in LANG_NAME_MAP
        url_lang = None
        if len(path_parts) > 0 and path_parts[0] in LANG_NAME_MAP:
            url_lang = path_parts[0]
        elif len(path_parts) > 1 and path_parts[1] in LANG_NAME_MAP:
            url_lang = path_parts[1]

        if url_lang:
            lang = url_lang
            logger.debug(f"Language set from URL: {lang}")
        else:
            lang = kwargs.get('lang', DEFAULT_LANG)
            logger.debug(f"Language not found in url. set from default or kwargs: {lang}")

        if lang not in AVAILABLE_LANGS:
            logger.info(f"Attempted to access unsupported language: {lang}")
            abort(404) 

        # Step 4: Set the chosen language
        lang_name = LANG_NAME_MAP.get(lang, LANG_NAME_MAP.get(DEFAULT_LANG))
        kwargs['lang'] = lang
        kwargs['lang_name'] = lang_name
        logger.debug(f"Set kwargs: lang-> {kwargs['lang']} lang_name-> {kwargs['lang_name']}")

        return func(*args, **kwargs)
    return decorated_function

# A generic function to handle errors
def handle_error(error, error_class, lang):
    @language_wrapper
    def inner_handle_error(*args, **kwargs):
        lang = kwargs.get('lang', DEFAULT_LANG)  # Now dynamic
        error_instance = error_class(lang=lang, field_name='')
        logger.error(red(f"{error_class.__name__} '{error_instance.message}'"))
        return error_instance.http_response()
    return inner_handle_error(error)

