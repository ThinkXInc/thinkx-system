#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# batch/backup_mongo_dump_test.py
#

import os

from nose.tools import eq_

from batch.backup_mongo_dump import BackupMongoDump
from general.config import Config
from models.history import History
from tools.app_testcase import AppTestCase


class BackupMongoDumpTestCase(AppTestCase):
    TEST_HISTORIES_NUM = 266

    @classmethod
    def setUpClass(cls):
        # set mongoclient, db
        super(BackupMongoDumpTestCase, cls).setUpClass()
        # restore test data
        os.system('mongorestore -h localhost:27017 -d thesystem-test {}'.format(
            Config.MONGO_DB_TEST_DUMPFILES_ROOT))
        return

    def test_backup(self):
        # データがあることを確認
        histories = History.findAll()
        eq_(len(histories), self.TEST_HISTORIES_NUM)

        # s3upload後削除無し
        backupMongoDump = BackupMongoDump(backup_before_days=-1, delete_data=False)
        backupMongoDump.run()

        histories = History.findAll()
        eq_(len(histories), self.TEST_HISTORIES_NUM)

        # s3upload後削除
        backupMongoDump = BackupMongoDump(backup_before_days=-1, delete_data=True)
        backupMongoDump.run()

        histories = History.findAll()
        eq_(len(histories), 0)

    @classmethod
    def tearDownClass(cls):
        # set mongoclient, db
        super(BackupMongoDumpTestCase, cls).tearDownClass()
        return
