#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/media_type.py
#
# MediaType enum
#
# generate
# class MediaType(EnumLocale):
#    AUDIO = "audio"
#    VIDEO = "video"
#    TEXT = "text"
#    OTHERS = "others"

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
    Record(u"AUDIO", u"audio", u"オーディオ", u"Audio"),
    Record(u"VIDEO", u"video", u"動画", u"Video"),
    Record(u"TEXT", u"text", u"テキスト", u"Text"),
    Record(u"OTHERS", u"others", u"その他", u"Others"),
    ]

d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
for _record in _records:
    name = _record.name
    value = _record.value
    d[name] = value
    __ja__[value] = _record.ja
    __en__[value] = _record.en

MediaType = EnumLocale('MediaType', d)
MediaType.__ja__ = __ja__
MediaType.__en__ = __en__