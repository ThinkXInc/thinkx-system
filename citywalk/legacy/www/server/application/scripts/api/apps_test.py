#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
# app_test.py
#
# unittest for api/app.py
#

import os
import unittest
from base64 import b64encode

from nose.tools import eq_, ok_

from general.config import Config
from tools.app_testcase import AppTestCase


class Fixture():
    @classmethod
    def basicauth_fixture(cls):
        credentials = b64encode('beta:cryptoxanthin'.encode('ascii'))
        return {
            'content-type': 'application/json',
            'Authorization': 'Basic ' + credentials.decode("ascii")
        }

    @classmethod
    def app_version_fixture(cls):
        return [
            {
                "app_type": "ios",
                "app_version": 'v1.1.1',
            },
            {
                "app_type": "android",
                "app_version": 'v2.1.2',
            },
        ]


class AdsAPITestCase(AppTestCase):
    IMAGE_FILE_PATH = Config.TEST_IMAGE_FILE_PATH

    @classmethod
    def setUpClass(cls):
        # set mongoclient, db
        super(AdsAPITestCase, cls).setUpClass()
        # restore test data
        os.system('mongorestore -h localhost:27017 -d thesystem-test {}'.format(
            Config.MONGO_DB_TEST_DUMPFILES_ROOT))
        return

    def test_1_app_version(self):
        """ 1. /app/version [GET]
            2. /app/version [POST]
            3. /app/version/check/<app_type> [GET]
        """

        get_response = self.get(f'/app/version')
        eq_(200, get_response.status_code)
        ok_('application/json' in get_response.headers['content-type'])
        response_json = self.json_from_response(get_response)
        eq_(response_json.get('ios_version'), '')
        eq_(response_json.get('android_version'), '')

        json_data = {"app_type": "ios", "app_version": "v1.1.1"}
        post_response = self.post(f'/app/version', json_data)
        eq_(200, post_response.status_code)
        ok_('application/json' in post_response.headers['content-type'])
        response_json = self.json_from_response(post_response)
        eq_(response_json.get('message'), 'Success')
        eq_(response_json.get('status'), 'OK')

        json_data = {"app_type": "android", "app_version": "v2.2.2"}
        post_response = self.post(f'/app/version', json_data)
        eq_(200, post_response.status_code)
        ok_('application/json' in post_response.headers['content-type'])
        response_json = self.json_from_response(post_response)
        eq_(response_json.get('message'), 'Success')
        eq_(response_json.get('status'), 'OK')

        get_response = self.get(f'/app/version')
        eq_(200, get_response.status_code)
        ok_('application/json' in get_response.headers['content-type'])
        response_json = self.json_from_response(get_response)
        eq_(response_json.get('ios_version'), "v1.1.1")
        eq_(response_json.get('android_version'), "v2.2.2")

        ios_response = self.get(f'/app/version/check/ios?app_version=v1.1.1')
        eq_(200, ios_response.status_code)
        ok_('application/json' in ios_response.headers['content-type'])
        response_json = self.json_from_response(ios_response)
        eq_(response_json.get('is_latest_version'), True)
        eq_(response_json.get('latest_app_version'), "v1.1.1")
        eq_(response_json.get('local_app_version'), "v1.1.1")

        ios_response = self.get(f'/app/version/check/ios?app_version=v1.1.2')
        eq_(200, ios_response.status_code)
        ok_('application/json' in ios_response.headers['content-type'])
        response_json = self.json_from_response(ios_response)
        eq_(response_json.get('is_latest_version'), False)
        eq_(response_json.get('latest_app_version'), "v1.1.1")
        eq_(response_json.get('local_app_version'), "v1.1.2")

        android_response = self.get(f'/app/version/check/android?app_version=v2.2.2')
        eq_(200, android_response.status_code)
        ok_('application/json' in android_response.headers['content-type'])
        response_json = self.json_from_response(android_response)
        eq_(response_json.get('is_latest_version'), True)
        eq_(response_json.get('latest_app_version'), "v2.2.2")
        eq_(response_json.get('local_app_version'), "v2.2.2")

        android_response = self.get(f'/app/version/check/android?app_version=v2.2.3')
        eq_(200, android_response.status_code)
        ok_('application/json' in android_response.headers['content-type'])
        response_json = self.json_from_response(android_response)
        eq_(response_json.get('is_latest_version'), False)
        eq_(response_json.get('latest_app_version'), "v2.2.2")
        eq_(response_json.get('local_app_version'), "v2.2.3")

        if __name__ == '__main__':
            unittest.main()
