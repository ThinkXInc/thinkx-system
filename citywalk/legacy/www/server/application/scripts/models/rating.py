#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/rating.py
#
# Rating model
#

import sys
sys.path.append('../')
import datetime as dt
from pymongo import ASCENDING, DESCENDING, HASHED
from libcommon.mongobase import MongoBase
from libcommon.enumlocale import EnumLocale
from bson import ObjectId
from models.enums.rating_type import RatingType


class Rating(MongoBase):
    __collection__ = 'rating'
    __structure__ = {
        '_id': ObjectId,
        'user_id': str,
        'rating_type': int,
        'utc_date': dt.datetime,
        'rate': int,
        'comment': str,
        'facility_id': str,
        'audio_content_id': str,
        'created': dt.datetime,
        'updated': dt.datetime
    }
    __required_fields__ = ['_id', 'rating_type']
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

    @classmethod
    def facility_rating(cls, facility_id):
        """Returns facility rating.

        Aggregate all ratings for the designated facility.

        returns:
            {
                'facility_id': facility_id,
                'rate_count': rate_count,  # number of votes
                'rate_average': rate_average  # average all rates
            }
        """
        n = cls.count()
        results = cls.aggregate(pipeline=[
            {"$match": {"facility_id": facility_id}},
            {"$group": {
                "_id": "$facility_id",
                "average": { "$avg" :"$rate"}
                }
            }])
        if len(results) > 0:
            rate_average = results[0]["average"]
            return {
                'facility_id': facility_id,
                'rate_count': n,
                'rate_average': rate_average
                }
        else:
            print(f"[Warning] aggregate failed {results}")

