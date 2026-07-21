#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/gender.py
#
# Gender enum
#
# generate
#   class Gender(EnumLocale):
#      MALE = 1
#      ...
#      __ja__ = {
#         1: '男性',
#         ...
#      }
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
    Record(u"MALE", "male", u"男性", u"Male"),
    Record(u"FEMALE", "female", u"女性", u"Female"),
    Record(u"OTHERS", "others", u"その他", u"Others"),
    ]

d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
for _record in _records:
    name = _record.name
    value = _record.value
    d[name] = value
    __ja__[int] = _record.ja
    __en__[int] = _record.en

Gender = EnumLocale('Gender', d)
Gender.__ja__ = __ja__
Gender.__en__ = __en__


