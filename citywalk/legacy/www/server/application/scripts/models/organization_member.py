#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/organization_member.py
#
# Organization model
#

import pymongo
from bson import ObjectId
import datetime
from libcommon.mongobase import MongoBase
from libcommon.enumlocale import EnumLocale
from helpers.validator import Validator
from models.enums.organization_member_role import OrganizationMemberRole


class OrganizationMember(MongoBase):
    __collection__ = 'organization_member'
    __structure__ = {
        '_id': ObjectId,      
        'session_id': int,  # incremental numeric id for sessions
        'organization_id': ObjectId,

        'first_name': str,
        'last_name': str,
        'email': str,
        'password': bytes,

        'role': int,  # ex) OrganizationMemberRole.ADMIN.name

        # mail verification
        'verified': bool,
        'mail_validation_code': str,
        'mail_validation_code_expired_datetime': datetime.datetime,
        'new_email': str,  # needs to swap email

        'password_reset_code': str,
        'password_reset_code_expiration': datetime.datetime,

        'created': datetime.datetime,
        'updated': datetime.datetime
    }
    __min_name_length__ = 1
    __max_name_length__ = 30
    __required_fields__ = [
        '_id', 'session_id', 'organization_id', 'role']
    __default_values__ = {
    }
    __validators__ = {
        'email': Validator.validate_email_format(),
        'first_name': Validator.validate_length(
            __min_name_length__, __max_name_length__,
            key_name='first_name'),
        'last_name': Validator.validate_length(
            __min_name_length__, __max_name_length__,
            key_name='last_name'),
    }
    __indexes__ = [
        [
            ("email", pymongo.HASHED),
        ]
    ]

    def response_json(self, excludes=['_id', 'password'], exclude_none=False):
        d = {}
        for key, val in self.items():
            if not exclude_none\
                    or (exclude_none and val is not None):
                if isinstance(val, ObjectId):
                    val = str(val)
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}

    def is_only_admin(self) -> bool:
        """Check if there's no other admin except this user.

        returns:
            is_only_admin (bool): returns True, if no other admin exist.
        """
        organization_members = OrganizationMember.find(
            {'organization_id': self.organization_id})
        others = [m for m in organization_members if m._id != self._id]
        if len([m for m in others
                if m.role == OrganizationMemberRole.ADMIN.value]) > 0:
            return True
        else:
            return False