#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# facebook_utils.py
#
# facebook sdkをwrapしたutil class
#

import facebook

from general.base_logger import BaseLogger
from general.config import Config


class FacebookUtils:
    APP_ID = Config.FACEBOOK_APP_ID
    APP_SECRET = Config.FACEBOOK_APP_SECRET

    @classmethod
    def is_valid_access_token(cls, access_token: str, facebook_id_from_arg: str, logger: BaseLogger):
        """access tokenの有効性をチェックする

        チェック項目
          1. access tokenが有効かどうか
          2. inputのfacebook idとaccess tokenに紐づくfacebook idが一致しているか

        備考
          local及びtest環境では常にTrueを返却する

        args:
            access_token: str # ユーザーのaccess token
            facebook_id_from_arg: str # inputのfacebook id
            logger: BaseLogger

        returns:
            is_valid: bool
        """
        # local,testではfacebookAPIでの認証を行わない
        if Config.env in ["test", "local"]:
            return True

        graph = facebook.GraphAPI()
        response = graph.debug_access_token(token=access_token, app_id=cls.APP_ID, app_secret=cls.APP_SECRET)
        logger.debug(response)
        if not response:
            return False
        data = response.get("data")
        # 現在有効なaccess_tokenかを確認
        # 有効期限が過ぎたorユーザーが変更しているなどの可能性
        if not data.get("is_valid"):
            return False

        # 引数のfacebook_idとFacebookAPIから取得したfacebook_idが一致しているから確認する
        # もし違う場合はaccess_tokenが偽装されている可能性がある
        facebook_from_access_token = data.get("user_id")
        if facebook_id_from_arg != facebook_from_access_token:
            return False

        return True
