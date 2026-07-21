#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/organization.py
#
# Organization model
#

import datetime
import pymongo
from bson import ObjectId
from libcommon.enumlocale import EnumLocale
from libcommon.mongobase import MongoBase
from helpers.validator import Validator
from models.enums.organization_type import OrganizationType


class Organization(MongoBase):
    __collection__ = 'organization'
    __structure__ = {
        '_id': ObjectId,

        'name': str,  # ex) ThinkX,Inc
        'type': str,  # ex) OrganizationType.other_companies.name
        'business_description': str,  # ex) A private boart charter for fishing.

        'keyname': str,  # identical kay name eg. thinkx

        'language': str,
        'zipcode': str,  # ex) 1060032
        'country': str,  # ex) Country.JP.name
        'city': str,  # ex) Minato-ku
        'province': str,  # ex) Tokyo
        'address1': str,  # ex) Roppongi 7-7-7
        'address2': str,  # ex) Tri-Seven Roppongi 8F

        'tel_country_code': str,  # ex) +81 or 81 (JP)
        'tel': str,  # ex) 08099990000

        'lat': float,  # latitude of the address ex) 35.6649716
        'lng': float,  # longtitude of the addresitemtypes ex) 139.7291616

        'address_sid': ObjectId,  # Address.sid for searching locale address

        'is_authenticated': bool,  # if true, enable to connect the bank account

        'created': datetime.datetime,
        'updated': datetime.datetime
    }
    __min_name_length__ = 1
    __max_name_length__ = 30
    __max_business_description_length__ = 150
    __required_fields__ = [
        '_id', 'name', 'type',
        'country', 'city', 'province', 'zipcode',
        'address1', 'lat', 'lng', 'tel_country_code', 'tel']
    __default_values__ = {
    }
    __validators__ = {
     'name': Validator.validate_length(
         __min_name_length__,
         __max_name_length__,
         key_name='name'),
     'business_description': Validator.validate_length(
         1,
         __max_business_description_length__,
         key_name='business_description'),
    }
    __indexes__ = [
        [
            ("name", pymongo.HASHED),
        ]
    ]

    def response_json(self, excludes=['_id', 'password'], exclude_none=False):
        d = {}
        for key, val in self.items():
            if not exclude_none or (exclude_none and val != None):
                if isinstance(val, ObjectId):
                    val = str(val)
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}

    @staticmethod
    def is_keyname_unique(keyname: str):
        if Organization.findOne({'keyname': keyname}):
            return True
        else:
            return False
