#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/item_type.py
#
# ItemType enum
#
# generate
# class ItemType(EnumLocale):
#     EXPERIENCE = "experience"
#     ...
#     __ja__ = {
#       "experience": "体験",


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
    Record(u"EXPERIENCE", "experience", u"体験", u"Experience"),
    Record(u"FOOD", "food", u"食事", u"Food"),
    Record(u"SOUVENIR", "souvenir", u"お土産", u"Souvenir"),
    Record(u"EVENT", "event", u"イベント", u"Event"),
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

ItemType = EnumLocale('ItemType', d)
ItemType.__ja__ = __ja__
ItemType.__en__ = __en__


