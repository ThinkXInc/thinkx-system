#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# commons.py
#

import sys
import datetime
from logging import getLogger, StreamHandler, Formatter, DEBUG, basicConfig


def configureLog(level=DEBUG, name=__name__):
    basicConfig(stream=sys.stderr)
    handler = StreamHandler()
    handler.setLevel(level)
    format = '%(asctime)s[%(levelname)s]%(filename)s:%(lineno)d: %(message)s'
    handler.setFormatter(Formatter(format))
    logger = getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger.debug


def datetimenow():
    # return datetime.datetime.now(tz=pytz.timezone('Asia/Tokyo'))
    return datetime.datetime.utcnow()
