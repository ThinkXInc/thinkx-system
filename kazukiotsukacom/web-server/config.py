#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# NOTE:
# always considering using yaml to express settings, 
# but in the end writing them in python files for flexibility 
# in terms of conditional branching, etc.
#

import os
import logging
from enum import Enum
from datetime import datetime
from os.path import dirname, abspath, join
from dotenv import load_dotenv
# Set logger
from libcommon.logger import Logger
logger = Logger('config.py')
logger.setLevel(logger.DEBUG)
from libcommon.color import *

class EnvironmentNotSpecified(Exception):
    pass

class MissingKeyError(Exception):
    """Raised when a required key is missing from .env file."""
    pass

def check_config(config, required_keys):
    """Function to check if all required configuration keys exist and are not None."""
    # Assuming `red` and `bold` are defined functions that color the text
    missing_or_none_keys = [key for key in required_keys if not hasattr(config, key) or getattr(config, key) is None]
    
    for key in required_keys:
        if hasattr(config, key):
            value = getattr(config, key)
            if value is None:
                # Log with error highlighting if value is None
                logger.error(red(f"Config.{key} is set but its value is None."))
            else:
                # Log with standard highlighting for info
                logger.debug(yellow(f"Config.{key}: {value}"))
        else:
            # Log missing keys with error highlighting
            logger.error(red(f"Config key '{key}' is missing."))

    if missing_or_none_keys:
        error_message = f"Missing or None configuration keys: {', '.join(missing_or_none_keys)}"
        logger.error(red(error_message))
        raise MissingKeyError(red(error_message))

class Config:
    # web-server/
    SRC_ROOT = dirname(abspath(__file__))
    # thinkx/ 
    PRJ_ROOT = dirname(SRC_ROOT)
    # web-server/locales
    LOCALES_ROOT = join(SRC_ROOT, 'locales')

    DOTENV_PATH = join(PRJ_ROOT, '.env')

    REQUIRED_KEYS = [
        'ENV',
        'FLASK_APP_SECRET_KEY',
    ]

    if os.path.exists(DOTENV_PATH):
        load_dotenv(DOTENV_PATH)

        # Check for required keys
        missing_keys = [key for key in REQUIRED_KEYS if key not in os.environ]
        if missing_keys:
            raise MissingKeyError(red(f"Missing keys in .env file: {', '.join(missing_keys)}"))
    else:
        print(red('[WARNING] no .env file exists in {}'.format(DOTENV_PATH)))

    env = os.environ.get("ENV")
    print(f".env path: {DOTENV_PATH}")
    print(f"environment detected in .env => "+bold(f"{env}"))

    ENV = env

    DEFAULT_LANG = 'en'
    FLASK_APP_SECRET_KEY = os.environ.get("FLASK_APP_SECRET_KEY")
    FLASK_MAX_CONTENT_LENGTH = 70000000

    AWS_PROFILE_NAME = 'quantz-system'
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")

    MAIL_SENDER = 'ThinkX Inc. <noreply@thinkxinc.com>'
    MAIL_REPLY_TO = 'inquiry@thinkxinc.com'  # necessary

    if env == "production":
        HOST_URL = "https://kazukiotsuka.com"
        LOG_LEVEL = logging.INFO

    elif env == "develop":
        HOST_URL = "http://localhost:8000"
        LOG_LEVEL = logging.DEBUG
    else:
        print('no env specified')
        raise EnvironmentNotSpecified