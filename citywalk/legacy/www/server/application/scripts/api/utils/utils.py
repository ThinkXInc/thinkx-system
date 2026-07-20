#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# api/utils/utils.py
#

from general.config import Config
from models.enums.language import Language


# NOTE: this method moved to locale.py
# def getlang(request):
#     """Get lang from HTTP request object.
# 
#     language is set by the format as below.
#     https://xxx.com/aa/?lang=ja
# 
#     if "?lang={}" doesn't exist in url, 
#     Config.DEFAULT_LANGUAGE is used.
# 
#     args:
#         - request (Flask Request Object)
# 
#     return:
#         - lang (str) : eg. ja
# 
#     """
#     lang = request.args.get('lang') \
#         if Language.is_valid_name(request.args.get('lang')) \
#         else Config.DEFAULT_LANGUAGE
#     return lang
 