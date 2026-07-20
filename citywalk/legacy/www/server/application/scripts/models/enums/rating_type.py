#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/rating_type.py
#
# RatingType enum
#
# generate
# class RatingType(EnumLocale):
#    CITYWALK = "citywalk"
#    ...
#    __ja__ = {
#        "citywalk": "CITYWALKサービス",
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
    Record(u"CITYWALK", u"citywalk", 
           u"CITYWALKサービス", u"CITYWALK Service"),
    Record(u"FACILITY", u"facility",
           u"施設", u"Facility"),
    Record(u"GUIDE_CONTENT", u"guide_content",
           u"ガイドコンテンツ", u"Guide Contents"),
    Record(u"ITEMS", u"items",
           u"商品", u"Items"),
]

d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
for _record in _records:
    name = _record.name
    value = _record.value
    d[name] = value
    __ja__[value] = _record.ja
    __en__[value] = _record.en

RatingType = EnumLocale('RatingType', d)
RatingType.__ja__ = __ja__
RatingType.__en__ = __en__