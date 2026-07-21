#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# helpers/s3.py
#
# utility functions for S3
#

import os
import logging
import botocore
from boto3.session import Session
from botocore.client import Config as AWSConfig
from general.config import Config

s3_session = Session(profile_name=Config.AWS_PROFILE_NAME)
s3_resource = s3_session.resource('s3')
s3_client = s3_session.client(
    's3',
    region_name=s3_session.region_name,
    config=AWSConfig(signature_version='s3v4'))

# NOTE: None of these outputs are None, because awscli doesn't set values as envs. 
# print(f'AWS_PROFILE: {os.environ.get("AWS_PROFILE")}')
# print(f'AWS_AVAILABILITY_ZONE: {os.environ.get("AWS_AVAILABILITY_ZONE")}')
# print(f'AWS_ACCESS_KEY_ID: {os.environ.get("AWS_ACCESS_KEY_ID")}')
# print(f'AWS_SECRET_ACCESS_KEY: {os.environ.get("AWS_SECRET_ACCESS_KEY")}')


def put_content(
    content, object_key: str, content_type: str,
    bucket=Config.S3_BUCKET_NAME_CONTENTS):
    """Put content to S3 bucket.

    args:
        - content (any) : 
        - object_key (string) : "{wavs/texts/videos}/{organization}/{index}/{file_name}"
        - content_type (string) : "audio/wav", "text/plain", "image/jpeg", "image/png", "video/mp4"

            https://stackoverflow.com/questions/9929940/correct-mime-type-for-mp4

        - bucket (string) :

    returns:
        - returned_url (string) : url with hash & expiration
    """
    # put object
    try:
        s3_resource.Bucket(bucket).put_object(
            Key=object_key, Body=content, ContentType=content_type)
    except botocore.exceptions.ClientError as error:
        logging.info.error(f'{error}')
        raise error
    except botocore.exceptions.ParamValidationError as error:
        logging.info.error(f'{error}')
        raise error
    else:
        get_object_url(bucket, object_key)


def put_content_from_path(
    local_path: str, object_key: str,
    content_type: str,
    bucket=Config.S3_BUCKET_NAME_CONTENTS):
    """Put local file to S3 bucket.

    args:
        - local_path (string) : file path in local
        - object_key (string) : "{wavs/texts/videos}/{organization}/{index}/{file_name}"
        - content_type (string) : "audio/wav", "text/plain", "image/jpeg", "image/png", "video/mp4"

            https://stackoverflow.com/questions/9929940/correct-mime-type-for-mp4

        - bucket (string) :

    returns:
        - returned_url (string) : url with hash & expiration
    """
    # put object
    return put_content(open(local_path, 'rb'), object_key, content_type, bucket)


def get_object_url(
    object_key: str, bucket=Config.S3_BUCKET_NAME_CONTENTS):
    """Put synthesized text to S3 bucket.

    args:
        - object_key (string) : "{wavs/texts/videos}/{organization}/{index}/{file_name}"
        - organization (string) :
        - index (int) :
        - lang (string) : ja|en|zh|..

    returns:
        - url (string) : url with hash & expiration

    """
    # get presigned url
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket, 'Key': object_key},
            ExpiresIn=3600)
    except botocore.exceptions.ClientError as error:
        logging.info.error(f'{error}')
        raise error
    except botocore.exceptions.ParamValidationError as error:
        logging.info.error(f'{error}')
        raise error
    else:
        return url


# texts

def put_text(
    text, organization='thinkx', index=1, lang='ja',
    bucket=Config.S3_BUCKET_NAME_CONTENTS):
    """Put synthesized text in /var/synth_results/ to S3 bucket.

    backet path:
        citywalk-contents/texts/{organization}/{index}/{organization}_{index}_{lang}.txt

    local path:
        /var/texts/{organization}/{index}_{lang}.txt

    args:
        - text (string) : text
        - organization (string) :
        - index (int) :
        - lang (string) : ja|en|zh|..

    returns:
        - returned_url (string) : url with hash & expiration

    """
    file_name, object_key = text_object_key(organization, index, lang)
    # put object & retrieve url in s3 with hash and expiration
    return put_content(
        text, object_key, 'plain/text', bucket)


def get_text_url(organization='thinkx', index=1, lang='ja'):
    """Put synthesized text to S3 bucket.

    args:
        - organization (string) :
        - index (int) :
        - lang (string) : ja|en|zh|..

    returns:
        - returned_url (string) : url with hash & expiration

    """
    file_name, object_key = text_object_key(organization, index, lang)
    # retrieve url in s3 with hash and expiration
    return get_object_url(object_key, 'citywalk-contents')


def text_object_key(organization='thinkx', index=1, lang='ja'):
    """S3 bucket path.

    args:
        - organization (string) :
        - index (int) :
        - lang (string) : ja|en|zh|..
    returns:
        - file_name (string) : s3 object key (file name)
        - object_key (string) : s3 object key (path)
    """
    file_name = f'{organization}_{index}_{lang}.txt'
    object_key = f'{organization}/texts/{index}/{file_name}'
    return file_name, object_key


# wavs

def put_wav_from_path(local_path, organization='thinkx', index=1, lang='ja'):
    """Put synthesized wav in /var/synth_results/ to S3 bucket.

    backet path:
        citywalk-contents/wavs/{organization}/{index}/{organization}_{index}_{lang}.wav

    local path:
        /var/synth_results/{organization}_{index}_{lang}.wav

    args:
        - local_path (string) : wav file path in local
        - organization (string) :
        - index (int) :
        - lang (string) : ja|en|zh|..

    returns:
        - returned_url (string) : url with hash & expiration

    """
    file_name, object_key = wav_object_key(organization, index, lang)
    # put object & retrieve url in s3 with hash and expiration
    return put_content_from_path(
        local_path, object_key, 'audio/wav', Config.S3_CI)


def get_wav_url(
    organization='thinkx', index=1, lang='ja',
    bucket=Config.S3_BUCKET_NAME_CONTENTS):
    """Put synthesized wav to S3 bucket.

    args:
        - organization (string) : Organization.keyname
        - index (int) :
        - lang (string) : ja|en|zh|..

    returns:
        - returned_url (string) : url with hash & expiration

    """
    file_name, object_key = text_object_key(organization, index, lang)
    # retrieve url in s3 with hash and expiration
    return get_object_url(object_key, bucket)


def wav_object_key(organization='thinkx', index=1, lang='ja'):
    """S3 bucket path.

    args:
        - organization (string) : Organization.keyname
        - index (int) :
        - lang (string) : ja|en|zh|..
    returns:
        - file_name (string) : s3 object key (file name)
        - object_key (string) : s3 object key (path)
    """
    file_name = f'{organization}_{index}_{lang}.wav'
    object_key = f'{organization}/wavs/{index}/{file_name}'
    return file_name, object_key

# images 

def put_image_from_path(
    local_path, organization='thinkx', index=1, number=1,
    bucket=Config.S3_BUCKET_NAME_CONTENTS):
    """Put synthesized image in /var/synth_results/ to S3 bucket.

    backet path:
        citywalk-contents/images/{organization}/{index}/{organization}_{index}_{number}.jpeg

    local path:
        /var/images/{organization}/{index}_{number}.jpeg

    args:
        - local_path (string) : image file path in local
        - organization (string) :
        - index (int) : content index
        - number (int) : image index number

    returns:
        - returned_url (string) : url with hash & expiration

    """
    file_name, object_key = image_object_key(organization, index, number)
    # put object & retrieve url in s3 with hash and expiration
    return put_content_from_path(
        local_path, object_key, 'image/jpeg', bucket)


def get_image_url(
    organization='thinkx', index=0, number=0,
    bucket=Config.S3_BUCKET_NAME_CONTENTS):
    """Put synthesized image to S3 bucket.

    args:
        - organization (string) :
        - index (int) : content index
        - number (int) : image index number

    returns:
        - returned_url (string) : url with hash & expiration

    """
    file_name, object_key = image_object_key(organization, index, number)
    # retrieve url in s3 with hash and expiration
    return get_object_url(object_key, bucket)


def image_object_key(organization='thinkx', index=0, number=0):
    """S3 bucket path.

    args:
        - organization (string) :
        - index (int) : content index
        - number (int) : image index number

    returns:
        - file_name (string) : s3 object key (file name)
        - object_key (string) : s3 object key (path)
    """
    file_name = f'{organization}_{index}_{number}.jpeg'
    object_key = f'{organization}/images/{index}/{file_name}'
    return file_name, object_key

