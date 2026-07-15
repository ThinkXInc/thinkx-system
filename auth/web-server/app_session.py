#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# app_session.py (auth)
#
# L-1 追随 (quantz-web Q-4 と同型): 依存注入版 session_helper を生成する中央定義。
# pre-v2.0.0 では libcommon の flask_helpers.py が
#   `from models.data.user import User, UnauthorizedAccessError, UserNotFoundError`
# とホストの User を import 時に引き込むレイヤ逆転を持っていた。v2.0.0 の
# make_session_helper(user_loader, on_no_session, on_user_not_found) はこれを解消し、
# アプリが自分の User 取得ロジックと例外を注入する。
#
# auth は make_session_helper の 2 番目の消費者 (docs/AUTH_TRACK.md の副次的利点)。
# user_loader は auth 自身の User 取得ロジックの移設であり、on_no_session /
# on_user_not_found は models/data/user.py が持つ auth 固有の例外を注入する。

from libcommon.web.flask_helpers import make_session_helper
from models.data.user import User, UnauthorizedAccessError, UserNotFoundError

session_helper = make_session_helper(
    user_loader=lambda uid: User.objects(id=uid).first(),
    on_no_session=UnauthorizedAccessError,
    on_user_not_found=UserNotFoundError,
)
