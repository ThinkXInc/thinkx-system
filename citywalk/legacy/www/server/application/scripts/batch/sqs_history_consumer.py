#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# batch/sqs_history_consumer.py
#
#

import sys
import os
module_path = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(str(module_path))
from models.history import History, ActionType
from bson import ObjectId
import boto3
import json
import helpers.dateutils as dateutils

client = boto3.client('sqs')
queue_url = "https://sqs.ap-northeast-1.amazonaws.com/027421896362/citywalk-queue-history"

BATCH_SIZE_LIMIT = 100
MAX_NUMBER_OF_MESSAGES = 10
VISIBILITY_TIMEOUT = 20
WAIT_TIME_SECONDS = 5


def consume_history():
    print('========== Consume History Batch Start ==========')
    consumed_num = 0
    for cnt in range(0, BATCH_SIZE_LIMIT):
        history_logs = []
        entries = []
        sqs_messages = client.receive_message(
            QueueUrl=queue_url, MaxNumberOfMessages=MAX_NUMBER_OF_MESSAGES, VisibilityTimeout=VISIBILITY_TIMEOUT, WaitTimeSeconds=WAIT_TIME_SECONDS)
        if "Messages" in sqs_messages:
            for message in sqs_messages["Messages"]:
                try:
                    message_body = json.loads(message["Body"])
                    message_body["_id"] = ObjectId()
                    message_body["utc_date"] = dateutils.iso8061_to_datetime(message_body["timestamp"])
                    del message_body["timestamp"]
                except Exception as e:
                    print(f"This message in queue could not be polled properly. \n message: {message}")
                    print(e)
                    continue
                else:
                    history_logs += [History(message_body)]
                    entries += [{"Id": message['MessageId'],
                             "ReceiptHandle": message['ReceiptHandle']}]
            save_data = History.bulk_insert(history_logs)
            if save_data is not None:
                print(f'saved {save_data}')
                delete_data = client.delete_message_batch(
                    QueueUrl=queue_url,
                    Entries=entries
                )
                print(f'delete from queue {delete_data}')
                consumed_num = consumed_num + int(save_data)
        else:
            print("There is no message on SQS.")
            print(sqs_messages)
            break
    print(f"{consumed_num} messages were consumed.")
    print('========== Consume History Batch End ============')


if __name__ == '__main__':
    try:
        consume_history()
    except Exception as e:
        raise e
