#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/day.py
#
# Day enum
#
# based on:
#
# generate
#   class Day(EnumLocale):
#      MON = 1
#      ...
#      __ja__ = {
#         1: '月曜日',
#         ...
#      }
#

from collections import namedtuple
from libcommon.enumlocale import EnumLocale

DayRecord = namedtuple(
    'DayRecord',
    [
        'key',  # Color.RED 
        'value',  # Color.RED.value
        'ja',  # 赤
        'en',  # Red
    ]
)

_records = [
    DayRecord(u"SUN", "1", u"日曜日", u"Sunday"),
    DayRecord(u"MON", "2", u"月曜日", u"Monday"),
    DayRecord(u"TUE", "3", u"火曜日", u"Tuesday"),
    DayRecord(u"WED", "4", u"水曜日", u"Wednesday"),
    DayRecord(u"THU", "5", u"木曜日", u"Thursday"),
    DayRecord(u"FRI", "6", u"金曜日", u"Friday"),
    DayRecord(u"SAT", "7", u"土曜日", u"Saturday"),
    ]

d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
for _record in _records:
    key = _record.key
    index = int(_record.value)
    d[key] = index
    __ja__[index] = _record.ja
    __en__[index] = _record.en

Day = EnumLocale('Day', d)
Day.__ja__ = __ja__
Day.__en__ = __en__


# add functions
def valid_list(days):
    """Check if all elements are valid values.

    args:
        - days (list) : eg. [1, 3, 5]
    """
    return len(set(Day.values() + days)) <= len(Day.itemlist())


setattr(Day, "valid_list", valid_list)
