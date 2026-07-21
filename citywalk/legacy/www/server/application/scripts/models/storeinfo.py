#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/seller.py
#
# Seller model
#

import pymongo
import datetime
from bson import ObjectId
from libcommon.enumlocale import EnumLocale
from libcommon.mongobase import MongoBase
from helpers.validator import Validator


class StoreInfo(MongoBase):
    __collection__ = 'seller'
    __structure__ = {
        '_id': ObjectId,

        'name': str,  # ex) ThinkX,Inc
        'type': int,  # OrganizationType ex) 5. OTHER_COMPANIES
        'phone': str,  # ex) 03-5562-3466
        'mail': str,  # ex) info@thinkxinc.com

        'country': int,  # ex) Country.JP.value
        'zipcode': str,  # ex) 1060032
        'city': str,  # ex) Minato-ku
        'province': str,  # ex) Tokyo
        'address1': str,  # ex) Roppongi 7-7-7
        'address2': str,  # ex) Tri-Seven Roppongi 8F
        'tel': str,  # must be number type character ex) 03

        'address_sid': ObjectId,  # Address.sid for searching locale address

        'created': datetime.datetime,
        'updated': datetime.datetime

    }
    __required_fields__ = [
        '_id', 'name', 'type',
        'city', 'address1', 'address2',
        'tel1', 'tel2', 'tel3'
        ]
    __default_values__ = {
    }
    __validators__ = {
        'name': Validator.validate_length('organization name', 0, 100),
        'tel1' : Validator.validate_numeric_format('tel 1'),
        'tel2' : Validator.validate_numeric_format('tel 2'),
        'tel3' : Validator.validate_numeric_format('tel 3'),

    }
    __indexes__ = [
        [
            ("name", pymongo.HASHED),
        ]
    ]

    def response_json(self, excludes=['_id']):
        d = {}
        for key, val in self.items():
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}
