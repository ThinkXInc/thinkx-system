#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/addresses.py
#
# Address Producer API:
#  /v1/addresses/location/gps?userId=\(userId)&facilityId=\(facility.id)&lat=\(lat)&lng=\(lng)&timestamp=\(timestamp)
#  /v1/addresses/location/hgps?userId=\(userId)&facilityId=\(facility.id)&hgx=\(hgx)&hgy=\(hgy)&timestamp=\(timestamp)


import sys

sys.path.append('../')
from flask_httpauth import HTTPBasicAuth
from flask import request, jsonify, Blueprint
from models.user import User
from models.organization import Organization
from models.content import Content
from models.storeinfo import StoreInfo
from models.item import Item
from api.api_response import ErrorResponse, ErrorCode
from api.responses.api_successes import OK
from api.responses.api_errors import UserNotFoundError, OrganizationNotFoundError, ItemNotFound, StoreInfoNotFound, \
    ContentNotFoundError, UnknownModelCollectionError
from bson import ObjectId
from boto3.session import Session
import json
from helpers.geolocator import Geolocator
from general.config import Config

session = Session(profile_name=Config.AWS_PROFILE_NAME)

client = session.client('sqs', region_name='ap-northeast-1')
queue_url = "https://sqs.ap-northeast-1.amazonaws.com/027421896362/citywalk-queue-address-test"

auth = HTTPBasicAuth()
basic_auth_users = {
    "citywalk": "klawytic"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_users:
        return basic_auth_users.get(username)
    return None


blueprint_addresses = Blueprint('addresses', __name__)

@blueprint_addresses.route('/v1/addresses/produce', methods=['POST'])
@auth.login_required
def address_producer():
    """Produce address API.
    method: post
    URI: /v1/addresses/produce

    Produce Address to AWS SQS.
    args:
      - user_id or organization_id or item_id or content_id or storeinfo_id (only one single param)
    """

    user_id = request.json.get('user_id', None)
    organization_id = request.json.get('organization_id', None)
    item_id = request.json.get('item_id', None)
    content_id = request.json.get('content_id', None)
    storeinfo_id = request.json.get('storeinfo_id', None)

    if user_id is not None:
        model = User.findOne({'_id': ObjectId(user_id)})
        try:
            model = User.findOne({'_id': ObjectId(user_id)})
        except Exception:
            raise UserNotFoundError()
    elif organization_id is not None:
        try:
            model = Organization.findOne({'_id': ObjectId(organization_id)})
        except Exception:
            raise OrganizationNotFoundError()
    elif item_id is not None:
        try:
            model = Item.findOne({'_id': ObjectId(item_id)})
        except Exception:
            raise ItemNotFound()
    elif content_id is not None:
        try:
            model = Content.findOne({'_id': ObjectId(content_id)})
        except Exception:
            raise ContentNotFoundError()
    elif storeinfo_id is not None:
        try:
            model = StoreInfo.findOne({'_id': ObjectId(storeinfo_id)})
        except Exception:
            raise StoreInfoNotFound()
    else:
        # 指定されたID、もしくはID自体が何も指定されなかった場合は下記のエラー
        raise UnknownModelCollectionError('address_produced_error')

    language = model['language']
    province = model['province']
    city = model['city']
    address1 = model['address1']
    country = model['country']

    geolocator = Geolocator()
    lat, lng = geolocator.get_lat_lng_from_address(province=province, city=city, address1=address1, language=language)

    sid = ObjectId()
    model['address_sid'] = sid

    address = {
        'user_id': user_id,
        'organization_id': organization_id,
        'item_id': item_id,
        'sid': str(sid),
        'content_id': content_id,
        'storeinfo_id': storeinfo_id,
        'language': language,
        'country': country,
        'lat': lat,
        'lng': lng,
    }

    sent_message = client.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps(address))

    model.update()

    return OK(sent_message, 'successfully saved location address.')
