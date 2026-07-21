#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/organization_type.py
#
# OrganizationType enum
#
# generate
# class OrganizationType(EnumLocale):
#    INDIVIDUALS = "individuals"
#    ...
#    __ja__ = {
#        "individuals": "個人",
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
    # TODO: correct english
    Record(u"INDIVIDUALS", u"individuals", 
           u"個人", u"Individuals"),
    Record(u"COMMERCIAL_FACILITIES", u"commertial_facilities",
           u"商業施設", u"Commercial Facilities"),
    Record(u"TOURISTIC_FACILITIES", u"touristic_facilities",
           u"観光施設", u"Touristic Facilities"),
    Record(u"LOCAL_PUBLIC_ENTITIES", u"local_public_entities",
           u"地方自治体", u"Local Public Entities"),
    Record(u"DMO", u"dmo_organizations", u"DMO団体",
           u"DMO(Destination Management Organization)"),
    Record(u"OTHER_COMPANIES", u"other_companies",
           u"その他企業等", u"Other Companies"),
    Record(u"OTHERS", "others", u"その他", u"Others"),
]

d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
for _record in _records:
    name = _record.name
    value = _record.value
    d[name] = value
    __ja__[value] = _record.ja
    __en__[value] = _record.en

OrganizationType = EnumLocale('OrganizationType', d)
OrganizationType.__ja__ = __ja__
OrganizationType.__en__ = __en__