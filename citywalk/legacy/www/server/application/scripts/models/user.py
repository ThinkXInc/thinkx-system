#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# user.py
#
# User model
#

import datetime
import pymongo
from bson import ObjectId
from libcommon.mongobase import MongoBase
from helpers.validator import Validator


class User(MongoBase):
    __collection__ = 'user'
    __structure__ = {
        '_id': ObjectId,

        'user_id': int,
        'email': str,
        'password': str,
        'first_name': str,
        'last_name': str,
        'gender': str,
        'birth': datetime.date,
        'nationality': str,
        'language': str,  # eg. Language.ja.name

        'zipcode': str,  # ex) 1060032
        'country': str,  # ex) Country.JP.name
        'city': str,  # ex) Minato-ku
        'province': str,  # ex) Tokyo
        'address1': str,  # ex) Roppongi 7-7-7
        'address2': str,  # ex) Tri-Seven Roppongi 8F
        'tel_country_code': str,  # ex) +81 or 81 (JP)
        'tel': str,  # ex) 08099990000

        'address_sid': ObjectId,  # Address.sid for searching locale address

        'mail_validation_code': str,
        'mail_validation_code_expiration': datetime.datetime,

        'facebook_id': str,
        'facebook_access_token': str,
        'facebook_username': str,

        # 'profile_image_base64': str,


        # password reset
        'password_reset_code': str,
        'password_reset_code_expiration': datetime.datetime,
        # 'reset_code': str,

        # mail verification
        'verified': bool,
        'mail_validation_code': str,
        'mail_validation_code_expiration': datetime.datetime,

        # change email
        # 'change_email': str,
        # 'change_email_verified': bool,
        # 'change_email_verify_code': str,
        # 'change_email_verify_code_expiration': dt.datetime,

        'created': datetime.datetime,
        'updated': datetime.datetime
    }
    __required_fields__ = ['_id', 'user_id']
    __default_values__ = {
        'verified': False
    }
    __validators__ = {
        'email': Validator.validate_email_format(),
        'first_name': Validator.validate_length( 0, 100,key_name='first_name'),
        'last_name': Validator.validate_length( 0, 100 ,key_name= 'last_name'),
    }
    __indexes__ = [
        [
            ("email", pymongo.HASHED),
        ],
        [
            ("facebook_id", pymongo.HASHED),
        ],
        [
            ("facebook_access_token", pymongo.HASHED),
        ],
    ]

    def response_json(self, excludes=['password', 'confirmation_code', 'mail_validation_code']):

        d = {}
        for key, val in self.items():
            if isinstance(val, ObjectId):
                val = str(val)
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}