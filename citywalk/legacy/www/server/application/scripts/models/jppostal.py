#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/jppostal.py
#
# JPPostal model
#

import pymongo
import datetime
from bson import ObjectId
from libcommon.enumlocale import EnumLocale
from libcommon.mongobase import MongoBase
from helpers.validator import Validator


class JPPostal(MongoBase):
    __collection__ = 'jppostal'
    __structure__ = {
        '_id': ObjectId,

        'zipcode': str,  # ex) 1020072 (no hyphen)
        'province': str,  # ex) 東京都
        'city': str,  # ex) 千代田区
        'area': str,  # ex) 飯田橋

        'province_kana': str,  # ex) トウキョウト
        'city_kana': str,  # ex) チヨダク
        'area_kana': str,  # ex) イイダバシ

        'municipality_code': str,  # 全国地方公共団体コード ex) 13101

        'one_area_with_multiple_zipcode': bool,  # 10. 一町域が二以上の郵便番号で表される場合の表示　（注3）　（「1」は該当、「0」は該当せず）
        'one_zipcode_with_multiple_area': bool,  # 13. 一つの郵便番号で二以上の町域を表す場合の表示　（注5）　（「1」は該当、「0」は該当せず）
        'has_chome': bool,  # 12. 丁目を有する町域の場合の表示　（「1」は該当、「0」は該当せず）

        'lat': float,
        'lon': float,

        'created': datetime.datetime,
        'updated': datetime.datetime

    }
    __required_fields__ = [
        '_id', 'zipcode', 'province', 'city',
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
