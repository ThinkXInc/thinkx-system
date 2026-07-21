#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# app_testcase.py
#
# TestCase base class
#

import os
import unittest
import main
from base64 import b64encode
import tempfile
import json
import redis
from pymongo import MongoClient
from tools.mongobase import MongoBase
from general.config import Config


class AppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up TestCase class.

        Set db as Config.MONGO_TEST_DB_NAME
        """
        # mongo client, db
        MongoBase.set_test_db_client(Config.MONGO_DB_URI_TEST, Config.MONGO_DB_NAME_TEST)
        return

    @classmethod
    def tearDownClass(cls):
        """Tear down TestCase class.

        Drop test db.
        And reset db as Config.MONGO_DB_NAME
        """
        # drop test db
        cls.flushMongoTestDB()
        # put db back to default
        MongoBase.reset_test_db_client()
        # flush redis test db
        cls.flushRedisTestDB()
        return

    def setUp(self):
        # flask
        self.db_fd, main.app.config['DATABASE'] = tempfile.mkstemp()
        main.app.config['TESTING'] = True
        main.app.config['SECRET_KEY'] = Config.FLASK_TEST_SECRET_KEY
        self.app = main.app.test_client()  # TEST HTTP client

    def tearDown(self):
        # flask
        os.close(self.db_fd)
        os.unlink(main.app.config['DATABASE'])
        main.app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY
        # flush redis test db
        # self.flushRedisTestDB()
        # flush mongo test db
        # self.__client.drop_database(Config.MONGO_DB_NAME_TEST)
        # TODO: 本当は都度初期化すべき

    def add_auth(self, headers):
        auth_header = {
            'Authorization': 'Basic ' +
            b64encode(
                bytes('{}:{}'.format(
                    Config.BASIC_AUTH_USER,
                    Config.BASIC_AUTH_PASS), 'ascii')).decode('ascii')
            }
        if headers:
            headers.update(auth_header)
        else:
            headers = auth_header
        return headers

    def post(self, url, data, data_type='json', headers=None, content_type=None, avoid_dump=False):
        if content_type is None:
            content_type = 'application/{type}'.format(type=data_type)

        if content_type.endswith('json') and not avoid_dump:
            data = json.dumps(data)

        headers = self.add_auth(headers)
        return self.app.post(
            url,
            data=data,
            content_type=content_type,
            headers=headers)

    def get(self, url, queries_dict=None, headers=None):
        headers = self.add_auth(headers)
        return self.app.get(
            url,
            query_string=queries_dict,
            headers=headers
        )

    def delete(self, url, data, data_type='json', headers=None):
        headers = self.add_auth(headers)
        if data_type == 'json':
            return self.app.delete(
                url,
                data=json.dumps(data),
                content_type='application/json',
                headers=headers)

    def json_from_response(self, response_object):
        return json.loads(response_object.data.decode('utf-8'))

    @classmethod
    def flushMongoTestDB(cls):
        MongoBase._client(Config.MONGO_DB_URI_TEST).drop_database(Config.MONGO_DB_NAME_TEST)

    @classmethod
    def flushRedisTestDB(cls):
        redis_session = redis.Redis(
            host=Config.REDIS_HOST_SESSION,
            port=Config.REDIS_PORT_SESSION,
            db=Config.REDIS_DB_NUMBER_SESSION)
        redis_session.flushdb()
        return
