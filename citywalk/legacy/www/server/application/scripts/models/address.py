#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/address.py
#
# Address model
#

import pymongo
import datetime
from bson import ObjectId
from libcommon.enumlocale import EnumLocale
from libcommon.mongobase import MongoBase
from helpers.validator import Validator


class Address(MongoBase):
    __collection__ = 'address'
    __structure__ = {
        '_id': ObjectId,
        # address search example:
        # > Address.findOne(
        # >   {'sid': organization.address_sid, 'language': 'ja'})
        #
        # {
        #  'collection': 'organization',
        #  'language': 'ja',
        #  'country': 'バハマ',
        #  'privince': 'ニュー・プロビデンス',
        #  'city': 'ナッソー',
        #  'address1': '2MG8+W6',
        #  ..
        # }
        'sid': ObjectId,  # common in multiple languages as search key

        'collection': str,  # mongodb collection name eg. 'organization'

        'language': str,  # ISO639 language codes defined in language.py eg. ja, en, zh_cn

        'country': str,  # ISO-3611 country code eg. JA
        'zipcode': str,  # eg. 1020072 (no hyphen)
        'province': str,  # eg. New York | 東京都
        'city': str,  # eg. Brooklyn | 港区
        'address1': str,  # ex) 277 Bedford Avenue | 六本木7-7-7

        'formatted_address': str,

        'lat': float,
        'lng': float,

        'created': datetime.datetime,
        'updated': datetime.datetime

    }
    __required_fields__ = [
        '_id', 'collection', 'language', 'country', 'zipcode', 'province', 'city', 'address1',
        ]
    __default_values__ = {
    }
    __validators__ = {
        'zipcode': Validator.validate_zipcode_format(allow_hyphen=False),
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
