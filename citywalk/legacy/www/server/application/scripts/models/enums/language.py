#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/language.py
#
# Language enum
#
# generate
#   class Language(EnumLocale):
#      JA = ja
#      ...
#      __ja__ = {
#         'ja': '日本語',
#         ...
#      }
#
#  These values (ja, en, zh,..) follows ISO 639.
#
#    ISO 639 - 1 standard language codes:
#    https://www.andiamo.co.uk/resources/iso-language-codes/
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
        'en_with_region',  # eg. Red(Dark)
    ]
)

_records = [
    # basic 4
    Record(u"JA", "ja", u"日本語", u"Japanese", "Japanese"),
    Record(u"EN", "en", u"英語", u"English", "English(Standard)"),
    Record(u"ZH", "zh", u"中国語", u"Chinese", "Chinese(PRC)"),
    Record(u"KO", "ko", u"韓国語", u"Korean", "Korean"),
    # europe 5
    Record(u"FR", "fr", u"フランス語", u"French", "French(Standard)"),
    Record(u"DE", "de", u"ドイツ語", u"German", "German(Standard)"),
    Record(u"RU", "ru", u"ロシア語", u"Russian", "Russian(Standard)"),
    Record(u"ES", "es", u"スペイン語", u"Spanish", "Spanish(Standard)"),
    Record(u"IT", "it", u"イタリア語", u"Italian", "Italian(Standard)"),
    # asia 6
    Record(u"VI", "vi", u"ベトナム語", u"Vietnamese", "Vietnamese(Standard)"),
    Record(u"TH", "th", u"タイ語", u"Thai", "Thai(Standard)"),
    Record(u"HI", "hi", u"ヒンディー語", u"Hindi", "Hindi(Standard)"),
    Record(u"ID", "id", u"インドネシア語", u"Indonesian", "Indonesian(Standard)"),
    Record(u"MS", "ms", u"マレーシア語", u"Malaysian", "Malaysian(Standard)"),
    Record(u"TL", "tl", u"タガログ語", u"Tagalog", "Tagalog(Standard)"),

    # chinese - dialects
    #zh_cn = 301  # Chinese(PRC)
    #zh_hk = 302  # Chinese(HongKong)
    #zh_sg = 303  # Chinese(Singapore)
    #zh_tw = 304  # Chinese(Taiwan)

    ## english - dialects
    #en_us = 201  # English(United States)
    #en_gb = 202  # English(United Kingdom)
    #en_au = 203  # English(Australia)
    #en_bz = 204
    #en_ca = 205
    #en_ie = 206
    #en_jm = 207
    #en_nz = 208
    #en_za = 209
    #en_tt = 210

    ]


d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
for _record in _records:
    name = _record.name
    value = _record.value
    d[name] = value
    __ja__[value] = _record.ja
    __en__[value] = _record.en

Language = EnumLocale('Language', d)
Language.__ja__ = __ja__
Language.__en__ = __en__