#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# others_test.py
#
# unittest for api/others.py
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


class OthersAPITestCase(AppTestCase):
    @classmethod
    def setUpClass(cls):
        # set mongoclient, db
        super(OthersAPITestCase, cls).setUpClass()
        # restore test data
        os.system('mongorestore -h localhost:27017 -d thesystem-test {}'.format(
            Config.MONGO_DB_TEST_DUMPFILES_ROOT))
        return

if __name__ == '__main__':
    unittest.main()
