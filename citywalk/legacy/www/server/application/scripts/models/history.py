#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/history.py
#
# History model
#
import sys
sys.path.append('../')
import datetime as dt
from pymongo import ASCENDING, DESCENDING, HASHED
from libcommon.mongobase import MongoBase
from libcommon.enumlocale import EnumLocale
from bson import ObjectId
from models.enums.action_type import ActionType


class History(MongoBase):
    __collection__ = 'history'
    __structure__ = {
        '_id': ObjectId,
        'user_id': str,
        'action_type': int,
        'lat': float,
        'lon': float,
        'hlat': float,
        'hlon': float,
        'hgx': float,
        'hgy': float,
        'px': float,
        'py': float,
        'utc_date': dt.datetime,
        'facility_id': str,
        'object_id': str,
        'question_id': str,
        'answer': str,
        'check_in_panel_id': str,
        'audio_content_id': str,
        'created': dt.datetime,
        'updated': dt.datetime
    }
    __required_fields__ = ['_id', 'action_type']
    __default_values__ = {
    }
    __indexes__ = [
        [
            ("timestamp", ASCENDING),
        ]
    ]

    def response_json(self, excludes=['_id']):
        d = {}
        for key, val in self.items():
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}
