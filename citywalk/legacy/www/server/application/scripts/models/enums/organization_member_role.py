#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/organization_member_role.py
#
# OrganizationMemberRole enum
#
# generate
# class OrganizationMemberRole(EnumLocale):
#    ADMIN = 0  # available "resource, billing, item, content"
#    ...
#    __ja__ = {
#        0: "管理者",
# 

from collections import namedtuple
from libcommon.enumlocale import EnumLocale


Record = namedtuple(
    'Record',
    [
        'name',  # eg. Color.RED 
        'value',  # eg. Color.RED.value
        'ja',  # eg. 赤
        'en',  # eg. Red
    ]
)

_records = [
    # Admin: available "resource, billing, item, content"
    Record(u"ADMIN", u"0", u"管理者", u"Administrator"),
    # Power User: available "item, content" | unavailable "resource, billing"
    Record(u"POWER_USER", u"1", u"担当者", u"Power user"),
    # Billing: available "billing" | unavailable "resource, item, content"
    Record(u"BILLING", u"2", u"会計", u"Billing reference user"),
]

d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
for _record in _records:
    name = _record.name
    index = int(_record.value)
    d[name] = index
    __ja__[index] = _record.ja
    __en__[index] = _record.en

OrganizationMemberRole = EnumLocale('OrganizationMemberRole', d)
OrganizationMemberRole.__ja__ = __ja__
OrganizationMemberRole.__en__ = __en__


# add function
def is_authorized_admin_action(role: int):
    """Check if the administrator action is authorized.

    args:
        - role (int) : OrganizationMember.role
    returns:
        - is_authorized (bool) :
    """
    return role > OrganizationMemberRole.ADMIN.value


setattr(OrganizationMemberRole, "is_authorized_admin_action",
        is_authorized_admin_action)