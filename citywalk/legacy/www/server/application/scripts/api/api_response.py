#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/api_response.py
#
# APIResponse model
#
# usage:
#
# except ValueError(e):
#    return json(
#      ErrorResponse(
#        {
#          "code": ErrorCode.INVALID_PARAMETER,
#          "reason": "invalidParameter",
#          "message": e
#        }).json()
#      )
#

import sys
from flask import jsonify
sys.path.append('../')
from libcommon.modelbase import ModelBase
from libcommon.enumlocale import EnumLocale


class SuccessCode(EnumLocale):
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    PARTIAL_INFORMATION = 203
    NO_CONTENT = 204  # The server successfully processed the request, and is not returning any content.


class ErrorCode(EnumLocale):
    # 4xx
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    # 5xx
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    

class SuccessResponse(ModelBase):
    """Success Response Format
    NOTE: Currently not used. because writing json in each handler is more obvious.

    return jsonify({
        'saved_data': user.response_json(),
        'user_id': user_id,
        'success': {
            'code': 201,
            'message': 'new user created.'
        } // <= create here
    }), 201
    """
    __structure__ = {
        'code': int,
        'message': str
    }
    __required_fields__ = ["saved_data", "success"]
    __default_values__ = {
        'saved_data': None
    }
    __validators__ = {
    }

    def json(self, excludes=[]):
        d = {}
        for key, val in self.items():
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}


class ErrorResponse(ModelBase):
    """Error Response Format.

    NOTE: wrapping only 'error' part. because writing json in each Error is more obvious.

    return jsonify({
        'saved_data': user.response_json(),
        'error': {
            'key': 'user_id',
            'code': ErrorCode.BAD_REQUEST.value,
            'reason': 'BAD_REQUEST',
            'message': f'{user_id} is invalid as user_id.'
        } // <= create here
    }), ErrorCode.BAD_REQUEST.value
    """
    __structure__ = {
        'key': str,
        'code': int,
        'reason': str,
        'message': str
    }
    __required_fields__ = ["code", "message"]
    __default_values__ = {}
    __validators__ = {}

    def json(self, excludes=[]):
        d = {}
        for key, val in self.items():
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}