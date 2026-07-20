#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/action_type.py
#
# ActionType enum
#
# generate
# class ActionType(EnumLocale):
#    UPDATE_GPS_LOCATION = 1
#    ...
#    __ja__ = {
#        1: "現在座標更新(GPS)",
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
    Record(u"GPS_LOCATION_UPDATED", u"gps_location_updated", 
           u"現在座標更新(GPS)", u"GPS Location Updated"),
    Record(u"APP_LAUNCHED", u"app_launched",
           u"アプリケーション起動", u"App Launched"),
    # TODO:
    # UPDATE_GPS_LOCATION = 1
    # UPDATE_HGPS_LOCATION = 2
    # UPDATE_PATHNET_LOCATION = 3
    # LAUNCH_APP = 100
    # ENTER_BACKGROUND = 101
    # TERMINATE_APP = 102
    # TAP_FACILITY = 200
    # START_GUIDE = 300
    # FINISH_GUIDE = 301
    # STOP_GUIDE = 303
    # CHECKIN = 302
    # PLAY_AUDIO_CONTENT = 400
    # STOP_AUDIO_CONTENT = 401
    # FINISH_AUDIO_COUNTENT = 402
    # ANSWER_QUESTION = 500

    # __ja__ = {
    #     1: "現在座標更新(GPS)",
    #     2: "現在座標更新(HGPS)",
    #     3: "現在座標更新(PATHNET)",
    #     100: "アプリケーション起動",
    #     101: "アプリケーションバックグラウンド移行",
    #     102: "アプリケーション終了",
    #     200: "Facility選択",
    #     300: "案内開始",
    #     301: "案内終了",
    #     302: "チェックイン",
    #     400: "コンテンツ再生",
    #     401: "コンテンツ停止",
    #     402: "コンテンツ再生完了",
    #     500: "質問に回答",
    # }
]

d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
for _record in _records:
    name = _record.name
    value = _record.value
    d[name] = value
    __ja__[value] = _record.ja
    __en__[value] = _record.en

ActionType = EnumLocale('ActionType', d)
ActionType.__ja__ = __ja__
ActionType.__en__ = __en__