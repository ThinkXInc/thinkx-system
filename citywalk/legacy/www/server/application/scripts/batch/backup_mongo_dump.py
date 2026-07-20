#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# batch/backup_mongo_dump.py
#
# mongoのデータをs3にBackupしmongoからはデータを削除する
#
#  ・Options
#    --delete_data   true:s3にbackup後,mongoのデータは削除する [default: prod & stg -> true , other -> false]
#    --backup_before_days リカバリ&テスト用 backup対象日数を選択 [default: Config.MONGO_BACKUP_BEFORE_DAYS]
#
#
import argparse
import subprocess
import sys
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))

from general.config import Config
from helpers.date_utils import DateUtils
from helpers.mdc import MDC
from helpers.s3_utils import S3Utils
from helpers.utils import Utils

from batch.batch_logger import BatchLogger

batch_logger = BatchLogger.get_logger(process_name='BACKUP_MONGO_DUMP')


class BackupMongoDump():
    def __init__(self, backup_before_days, delete_data=False):
        self.delete_data = delete_data
        self.tmp_dir = f"/tmp/{MDC.get_message_id()}"
        self.target_date = DateUtils.get_n_days_ago_date(n_days=backup_before_days)
        # TODO mongoのtimezoneを設定したあと再度チェックする, dataが抜け落ちる可能性がある
        self.target_date_str = DateUtils.get_date_str(self.target_date, format="%Y-%m-%dT%H:%M:%S+09:00")
        batch_logger.info(f"delete_data: {self.delete_data}")
        batch_logger.info(f"tmp_dir: {self.tmp_dir}")
        batch_logger.info(f"target_date: {self.target_date_str}")

    def run(self):
        s3_dir = f'{DateUtils.get_date_str(format="%Y-%m-%d-%H%M%S")}-{MDC.get_message_id()}'
        cmd_query = f"{{ updated: {{$lte: ISODate('{self.target_date_str}') }}}}"
        for backup_collection in Config.MONGO_BACKUP_COLLECTIONS:
            # definition
            collection_name = backup_collection["collection_name"]
            package_name = backup_collection["package_name"]
            class_name = backup_collection["class_name"]
            __import__(str(package_name))
            model_cls = getattr(sys.modules[package_name], class_name)
            json_file_name = f"{collection_name}.json"

            # dumpファイルをlocalに出力
            batch_logger.info(f"started backup: {collection_name}")
            batch_logger.info(f"started mongodump: {collection_name}")
            output = subprocess.check_output(
                [
                    "mongoexport",
                    "--uri", Config.MONGO_DB_URI,
                    "--collection", collection_name,
                    "--out", f"{self.tmp_dir}/{json_file_name}",
                    "--query", cmd_query
                ]
            )
            batch_logger.info(f"finished mongodump: {collection_name}")

            # dumpファイルをs3に転送
            batch_logger.info(f"started updload s3: {collection_name}")

            subprocess.check_output(["gzip", f"{self.tmp_dir}/{json_file_name}"])
            S3Utils.upload_local_to_s3(
                s3_bucket=Config.MONGO_BACKUP_S3_BUCKET,
                src=f"{self.tmp_dir}/{json_file_name}.gz",
                dest=f"{s3_dir}/{json_file_name}.gz"
            )
            batch_logger.info(f"finished updload s3: {collection_name}")

            # localのdumpファイルを削除
            batch_logger.info(f"started remove local dump: {collection_name}")
            subprocess.check_output(["rm", "-fr", self.tmp_dir])
            batch_logger.info(f"started remove local dump: {collection_name}")

            # mongoのdataを削除
            if self.delete_data:
                query = {
                    "updated":
                        {
                            "$lte": self.target_date
                        }
                }
                batch_logger.info(f'started remove mongo data: {collection_name}')
                result = model_cls.delete(query)
                batch_logger.info(f'finished remove mongo data: {collection_name} applied:{result}')
            batch_logger.info(f"finished backup: {collection_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete_data", nargs=1)
    parser.add_argument("--backup_before_days", nargs=1)
    args = parser.parse_args()
    delete_data = False
    if Config.env in ["prod", "staging"]:
        delete_data = True
    if args.delete_data:
        delete_data = Utils.castStringToBool(args.delete_data[0])

    backup_before_days = Config.MONGO_BACKUP_BEFORE_DAYS
    if args.backup_before_days:
        backup_before_days = int(args.backup_before_days[0])

    backupMongoDump = BackupMongoDump(backup_before_days, delete_data=delete_data)
    backupMongoDump.run()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        batch_logger.error_traceback()
    finally:
        batch_logger.output_performance()
