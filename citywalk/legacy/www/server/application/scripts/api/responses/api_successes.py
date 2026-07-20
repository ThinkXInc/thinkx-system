#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/responses/api_successes.py
#
#

from flask import jsonify
from api.api_response import SuccessResponse, SuccessCode


# General Format

class APISuccess:
    __message__ = ''
    __http_success__ = SuccessCode.OK

    def __init__(self, saved_data, message):
        self.__saved_data__ = saved_data
        self.__message__ = message
        
    def json(self) -> tuple:
        return jsonify(
            {
                'saved_data': self.__saved_data__,
                'success': SuccessResponse({
                    'code': self.__http_success__.value,
                    'message': self.__message__
                }).json()
            }), self.__http_success__.value

    def __str__(self):
        return repr(self.__message__)


# Specific Patterns

class OK(APISuccess):
    __http_success__ = SuccessCode.OK

    def __init__(self, message):
        self.__saved_data__ = None
        self.__message__ = message


class CREATED(APISuccess):
    __http_success__ = SuccessCode.CREATED

    def __init__(self, saved_data, message):
        self.__saved_data__ = saved_data
        self.__message__ = message

