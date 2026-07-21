#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/user.py
#
# unittest for User model

from nose.tools import eq_, ok_

from models.user import User
from tools.app_testcase import AppTestCase


class Fixture():
    @classmethod
    def user_fixture(cls):
        return [
            {
                '_id': 1,
                'email': 'mail@mail.com
            },
    ]


class UserTestCase(AppTestCase):
    def test_1_save(self):
        """1. User.save()
        """
        for user_dict in Fixture.user_fixture():
            User(user_dict).save()
            user = User.findOne({'_id': user_dict['_id']})
            eq_(user.email, user_dict['email'])
