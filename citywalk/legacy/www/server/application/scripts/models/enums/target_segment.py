#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/target_segment.py
#
# TargetSegment enum
#
# generate
# class TargetSegment(EnumLocale):
#     # generation
#     EVERYONE = "everyone"
#     ADULTS = "adults"
#     CHILDREN = "children"
#     YOUNGERS = "youngers"
#     ELDERS = "elders"
#     # education
#     EDUCATED = "educated"
#     # gender
#     MALES = "males"
#     FEMALES = "females"


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
    # generation
    Record(u"EVERYONE", u"everyone", u"全員", u"Everyone"),
    Record(u"ADULTS", u"adults", u"大人", u"Adults"),
    Record(u"CHILDREN", u"children", u"子供", u"Children"),
    Record(u"YOUNGERS", u"youngers", u"若者", u"Younger Generations"),
    Record(u"ELDERS", u"elders", u"高齢者", u"Elder People"),
    # education
    Record(u"EDUCATED", u"educated", u"教養層", u"Educated people"),
    # gender
    Record(u"MALES", u"males", u"男性", u"Males"),
    Record(u"FEMALES", u"females", u"女性", u"Females"),
    ]

d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
for _record in _records:
    name = _record.name
    value = _record.value
    d[name] = value
    __ja__[value] = _record.ja
    __en__[value] = _record.en

TargetSegment = EnumLocale('TargetSegment', d)
TargetSegment.__ja__ = __ja__
TargetSegment.__en__ = __en__