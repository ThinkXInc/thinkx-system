#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# batch/sqs_address_consumer.py
#
#

import sys
import os
module_path = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(str(module_path))
from models.address import Address
from bson import ObjectId
from boto3.session import Session
from general.config import Config
import json
import logging
from helpers.geolocator import Geolocator
import re
from batch.batch_errors import BatchError, UnknownModelCollectionError

session = Session(profile_name=Config.AWS_PROFILE_NAME)

client = session.client('sqs', region_name='ap-northeast-1')
queue_url = f"{os.environ['SQS_ENDPOINT']}citywalk-queue-address-test"
print(queue_url)


BATCH_SIZE_LIMIT = 100  # Maximum number of consumed address per excuting batch
MAX_NUMBER_OF_MESSAGES = 10  # Maximum amount to consume address from SQS
VISIBILITY_TIMEOUT = 20
WAIT_TIME_SECONDS = 5


def consume_address():
    """Consume address from SQS and insert to DB.

    args:
        - None

    returns:
        - void
    """
    print('========== Start Consuming Address ==========')
    consumed_num = 0
    for cnt in range(0, BATCH_SIZE_LIMIT):
        entries = []
        sqs_messages = client.receive_message(
            QueueUrl=queue_url, MaxNumberOfMessages=MAX_NUMBER_OF_MESSAGES, VisibilityTimeout=VISIBILITY_TIMEOUT, WaitTimeSeconds=WAIT_TIME_SECONDS)
        if "Messages" in sqs_messages:
            for message in sqs_messages["Messages"]:
                try:
                    message_body = json.loads(message["Body"])
                except Exception as e:
                    print(f"This message in queue could not be polled properly. \n message: {message}")
                    print(e)
                    continue
                else:
                    entries += [{"Id": message['MessageId'],
                                "ReceiptHandle": message['ReceiptHandle']}]
            save_data = save_addresses(message_body)
            if save_data is not None:
                print(f'saved {save_data}')
                delete_data = client.delete_message_batch(
                    QueueUrl=queue_url,
                    Entries=entries
                )
                print(f'delete from queue {delete_data}')
                consumed_num = consumed_num + len(delete_data['Successful'])
        else:
            print("There is no message on SQS.")
            print(sqs_messages)
            break
    print(f"{consumed_num} messages were consumed.")
    print('========== End Consuming Address ============')


def save_addresses(consumed_address_data):
    """Insert address to DB.

    args:
        - consumed_address_data: dict

    returns:
        - the result of bulk_insert
    """
    geolocator = Geolocator()
    address_list = []
    with open(f'{module_path}models/data/address/address_formats.json') as f:
        address_formats = json.load(f)
        address_format = address_formats.get(consumed_address_data['language'].upper())
        sid = ObjectId(consumed_address_data['sid'])
        for language_name in address_formats.keys():
            address = geolocator.get_address_from_lat_lng(consumed_address_data['lat'], consumed_address_data['lng'], language_name)
            address_components = address['address_components']

            # format address from geolocator data
            province, city, address1 = format_address(consumed_address_data, address_components, address_format)

            consumed_address_data['_id'] = ObjectId()
            consumed_address_data['sid'] = sid
            consumed_address_data['language'] = language_name
            consumed_address_data['country'] = filter_address(filter_str='country', address_components=address_components, name_key='short_name')[0]
            consumed_address_data['zipcode'] = filter_address(filter_str='postal_code', address_components=address_components)[0]
            consumed_address_data['zipcode'] = consumed_address_data['zipcode'].replace('-', '')
            consumed_address_data['formatted_address'] = address['formatted_address']
            consumed_address_data['province'] = province
            consumed_address_data['city'] = city
            consumed_address_data['address1'] = address1

            # judge collection type
            if consumed_address_data.get('user_id') is not None:
                consumed_address_data['collection'] = 'user'
            elif consumed_address_data.get('organization_id') is not None:
                consumed_address_data['collection'] = 'organization'
            elif consumed_address_data.get('item_id') is not None:
                consumed_address_data['collection'] = 'item'
            elif consumed_address_data.get('content_id') is not None:
                consumed_address_data['collection'] = 'content'
            elif consumed_address_data.get('storeinfo_id') is not None:
                consumed_address_data['collection'] = 'storeinfo'
            else:
                raise UnknownModelCollectionError('valid collection id is not included.')

            # delete the keys which is not necessary
            for key in list(consumed_address_data.keys()):
                if consumed_address_data[key] is None:
                    del consumed_address_data[key]

            address_list += [Address(consumed_address_data)]

    return Address.bulk_insert(address_list)


def filter_address(filter_str, address_components, name_key='long_name'):
    """Filter address from address_components.

    args:
        - filter_str: str
        - address_components: dict
        - name_key: str

    returns:
        - list of filtered address
    """
    filtered_components = list(filter(lambda item: len([s for s in item['types'] if s.startswith(filter_str)]) > 0, address_components))
    if len(filtered_components) == 0:
        return None
    elif len(filtered_components) > 1:
        filtered_components = sorted(filtered_components, key=natural_keys)
        full_name_list = []
        for component in filtered_components:
            full_name_list.append(component[name_key])
        return full_name_list
    else:
        return [filtered_components[0][name_key]]


def natural_keys(component):
    """ Sort address values by '_level_'.

    args:
        - consumed_address_data: str
        - address_component: str

    returns:
        - province:str
        - city: str
        - address1: str
    """
    target_type = [s for s in component['types'] if '_level_' in s]
    return [int(text) if text.isdigit() else text for text in re.split(r'(\d+)', target_type[0])]


def format_address(consumed_address_data, address_components, address_format):
    """Format address from address_components to province, city and address1.

    args:
        - consumed_address_data: str
        - address_component: str

    returns:
        - province:str
        - city: str
        - address1: str
    """
    delimiter = ','
    if consumed_address_data['country'] == 'JP':
        delimiter = '-'
    if address_format is None:
        return

    province = []
    for address_type in address_format['province']:
        part_of_province = filter_address(filter_str=address_type, address_components=address_components)
        if part_of_province is None:
            continue
        province.extend(part_of_province)
    province = delimiter.join(province)

    city = []
    for address_type in address_format['city']:
        part_of_city = filter_address(filter_str=address_type, address_components=address_components)
        if part_of_city is None:
            continue
        city.extend(part_of_city)
    city = delimiter.join(city)

    address1 = []
    for address_type in address_format['address1']:
        part_of_address1 = filter_address(filter_str=address_type, address_components=address_components)
        if part_of_address1 is None:
            continue
        address1.extend(part_of_address1)

    if consumed_address_data['country'] == 'JP' and consumed_address_data['language'] == 'ja':
        address1 = jp_address1(address1)
    elif consumed_address_data['country'] == 'JP' and consumed_address_data['language'] != 'ja':
        town = address1[-1]
        address1 = address1[:-1]
        address1 = delimiter.join(address1)
        address1 = f'{address1} {town}'
    else:
        address1 = delimiter.join(address1)

    return province, city, address1


def jp_address1(address1):
    """Format address for JP.

    args:
        - address1: list

    returns:
        - str
    """
    if len(address1) == 4:
        return f'{address1[3]}{address1[0]}-{address1[1]}-{address1[2]}'
    else:
        return f'{address1[2]}{address1[0]}-{address1[1]}'


if __name__ == '__main__':
    try:
        consume_address()
    except Exception as e:
        raise BatchError(e)
