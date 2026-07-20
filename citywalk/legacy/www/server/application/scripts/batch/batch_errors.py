#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# batch/batch_errors.py
#
# BatchError
# NotCollectionError

import re
from flask import jsonify
from api.api_response import ErrorResponse, ErrorCode
from general.config import Config
from helpers.locale import Locale

# locale object with errors.json
locale = Locale(f'{Config.MESSAGES_ROOT}/errors.json')
# the function message(key, lang, *args)
message = locale.message


# camelcase to snake case
def snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


class BatchError(Exception):
    __key__ = ''
    __message__ = ''

    def __init__(self, key, value):
        self.value = value
        self.__key__ = key
        self.__message__ = ''

    def __error__(self) -> dict:
        return {
                'key': self.__key__,
                'message': self.__message__
               }

    def __error_obj__(self) -> tuple:
        error_response = ErrorResponse(self.__error__())
        return jsonify(
            {
                'saved_data': None,
                'error': error_response.json()
            })

    def __str__(self):
        return repr(self.__message__)


class UnknownModelCollectionError(BatchError):

    def __init__(self, message, lang="en"):
        self.__message__ = message
