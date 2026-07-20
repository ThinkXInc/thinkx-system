#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/content.py
#
# Content model
#

import pymongo
from bson import ObjectId
import datetime
from libcommon.enumlocale import EnumLocale
from libcommon.mongobase import MongoBase
from helpers.validator import Validator
from models.enums.media_type import MediaType
from models.enums.target_segment import TargetSegment


class Content(MongoBase):
    __collection__ = 'content'
    __structure__ = {
        '_id': ObjectId,
        'index': int,  # eg. 12
        'media_type': str,  # eg. MediaType.AUDIO_GUIDE.name

        # 'objective_id': ObjectId,  # to which objective is related

        'lat': float,
        'lon': float,

        'label': str,  # eg. Giza Pyramid
        'title': str,  # eg. The secret of Giza Pyramid
        'text': str,  # eg. The Great Pyramid of Giza is the oldest pyramids in the Giza pyramid complex

        'resource_key': str,  # eg. {organization_id}_{index}_{lang}.wav
        'image_key': str,  # eg. {organization_id}_{index}.jpg

        'language': str,  # eg. Language.ja.name

        'organization_id': str,  # The organization who registered this idea. ex) Organization._id

        'target': int,  # TargetSegment
        'radius': int,  # detection range
        'condition': dict,  # condition that this idea is reached. for instance, age restriction
        'featured': bool,  # featured flag
        'importance': int,  # publishing priority

        'created_member_id': ObjectId,  # _id of the member who created this idea  
        'latest_edit_member_id': ObjectId,  # _id of the member who last edited this idea  

        'deleted': bool,  # True when user chose deleting. after deleted, hidden but enable to recover.

        'created': datetime.datetime,
        'updated': datetime.datetime
    }
    __min_name_length__ = 1
    __max_name_length__ = 30
    __min_title_length__ = 3
    __max_title_length__ = 100
    __min_text_length__ = 20
    __max_text_length__ = 100
    __required_fields__ = ['_id', 'name', 'title', 'text', 'media_type', 'country']
    __default_values__ = {
        'deleted': False
    }
    __validators__ = {
        'name': Validator.validate_length('name', __min_name_length__, __max_name_length__),
        'title': Validator.validate_length('title', __min_title_length__, __max_title_length__),
        'text': Validator.validate_length('text', __min_text_length__, __max_text_length__),
    }
    __indexes__ = [
        [
            ("name", pymongo.HASHED),
        ]
    ]

    def response_json(self, excludes=[]):
        d = {}
        for key, val in self.items():
            if isinstance(val, ObjectId):
                val = str(val)
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}

    @classmethod
    def fetch(cls, organization_id: ObjectId, with_deleted=False, json=True):
        """Fetch all ideas of the organization.

        args:
            - organization_id (ObjectId) : 
            - with_deleted (bool) : fetch deleted items if True
            - json (bool) : return by json if True

        returns:
            - ideas (list) : list of Idea objects
        """
        if with_deleted:
            ideas = cls.find({'organization_id': organization_id})
        else:
            ideas = cls.find({'organization_id': organization_id}, {"deleted": {"$ne": True}})
        if json:
            return [c.response_json() for c in ideas]
        else:
            return ideas

    @classmethod
    def validate_name_length(cls, name: str):
        if name < cls.__max_name_length__ and name > cls.__min_name_length__:
            return True
        else:
            return False

    @classmethod
    def validate_title_length(cls, title: str):
        if title < cls.__max_title_length__ and title > cls.__min_title_length__:
            return True
        else:
            return False

    @classmethod
    def validate_text_length(cls, text: str):
        if text < cls.__max_text_length__ and text > cls.__min_text_length__:
            return True
        else:
            return False