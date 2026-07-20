#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/items.py
#

import re
import sys
import logging
import datetime
from bson import ObjectId
from flask import jsonify, Blueprint, request
from flask_httpauth import HTTPBasicAuth
sys.path.append('../')
from helpers.validator import Validator
from api.api_response import SuccessResponse, ErrorResponse, SuccessCode, ErrorCode
from api.responses.api_errors import SessionDoesntExistError, InvalidContentType, \
    SaveError, OrganizationMemberNotFoundError, ContentNotFoundError, \
    InvalidNameLength, InvalidDescriptionLength ,InvalidItemType, \
    InvalidLatLonError 
from helpers.mail import Mail
from helpers.s3 import put_text
from helpers.dateutils import expiration_datetime
from models.organization import Organization
from models.item import Item, TimeTable
from models.enums.item_type import ItemType
from models.enums.day import Day
from models.enums.language import Language
from tools.sessions import OrganizationMemberSession


auth = HTTPBasicAuth()
basic_auth_items = {
    "<REDACTED>": "<REDACTED>"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_items:
        return basic_auth_items.get(username)
    return None


blueprint_items = Blueprint('items', __name__)


# ERROR Handlers

@blueprint_items.errorhandler(SessionDoesntExistError)
@blueprint_items.errorhandler(InvalidContentType)
@blueprint_items.errorhandler(SaveError)
@blueprint_items.errorhandler(OrganizationMemberNotFoundError)
@blueprint_items.errorhandler(ContentNotFoundError)
@blueprint_items.errorhandler(InvalidNameLength)
@blueprint_items.errorhandler(InvalidDescriptionLength)
def error_response(error):
    error_reponse = error.__error_obj__()
    return error_reponse


# API Handlers

@blueprint_items.route('/v1/items/create', methods=['POST'])
def items_create():
    """Create new item.

    /v1/items/create [POST]

    params:
        - name (str) : 
        - description (str) :
        - price (int) :
        - item_type (int) : ItemType.value
        - lat (float) :
        - lon (float) :
        - store_info_id (str) : StoreInfo._id
        - reservable (bool) : True if the item needs reservations
        - available_days (list) : list of Day.value
        - start_time (str) : eg. 9:00 (by 30 minutes)
        - end_time (str) : eg. 23:30 (by 30 minutes)
    """
 
    logging.info('/v1/items/create [POST]')
    logging.info(request.json)

    # check request header
    if request.headers['Content-Type'] not in ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    name = request.json.get('name', type=str)
    description = request.json.get('description', type=str)
    price = request.json.get('price', type=int)
    item_type = request.json.get('item_type', type=int)
    lat = request.json.get('lat', type=float)
    lon = request.json.get('lon', type=float)
    reservable = request.json.get('reservable', type=bool)
    store_info_id = request.json.get('store_info_id', type=str)
    available_days = request.json.get('available_days', type=list)
    start_time = request.json.get('start_time', type=str) 
    end_time = request.json.get('end_time', type=str) 

    logging.info(f'new item submitted \nname: {name}\nitem_type: {item_type}\nlat: {lat}\nlon: {lon}')

    # check parameters
    if not Item.validate_name_length(name):
        raise InvalidNameLength(
            name, Item.__min_name_length__, Item.__max_name_length__)
    if not Item.validate_description_length(description):
        raise InvalidDescriptionLength(
            description, Item.__min_description_length__, Item.__max_description_length__)
    if item_type in ItemType.values():
        raise InvalidItemType(item_type)
    if isinstance(lat, float) or isinstance(lon, float):
        raise InvalidLatLonError(lat, lon)
    if Day.valid_list(available_days):
        raise InvalidAvailableDays(available_days)
    if re.match(Validator.hhmm_30min_regex, start_time):
        raise InvalidTime(start_time)
    if re.match(Validator.hhmm_30min_regex, end_time):
        raise InvalidTime(end_time)
    if not StoreInfo.findOne({'_id': store_info_id}):
        raise StoreInfoNotFound(store_info_id)

    # user_id from context
    user_id = OrganizationMemberSession.user_id()
    if not user_id:
        raise SessionDoesntExistError()

    # fetch user
    organization_member = OrganizationMemberSession.findOne({'_id': user_id})
    if not organization_member:
        raise OrganizationMemberNotFoundError(user_id)
    logging.debug(
        f'organization_member {organization_member._id} found by session_id {user_id}.')

    # fetch organization
    organization_id = organization_member.organization_id
    organization = Organization.findOne({'_id': organization_id})
    if not organization:
        raise OrganizationNotFoundError(organization_id)
    logging.debug(
        f'organization {organization._id} found by organization_id {organization_id}.')

    # generate item_id
    item_id = ObjectId()

    # generate time table
    years = [y for y in range(datetime.datetime.now().year, datetime.datetime.now().year+5)]
    time_tables = [TimeTable({
        'label': f'{name}_{year}',
        'year': year,
        'organization_id': organization_id,
        'item_id': item_id
        }).init() for year in years]

    # save Organization/OrganiationMember account
    item = Item({
        '_id': item_id,
        'item_type': item_type,
        'name': name,
        'description': description,
        'organization_id': organization_member.organization_id,
        'store_info_id': store_info_id,
        'reservable': reservable,
        'time_table_ids': [time_table._id for time_table in time_tables],
        'created_member_id': organization_member._id,
        'latest_edit_member_id': organization_member._id,
    })

    # save organization
    try:
        for time_table in time_tables:
            time_table.save()
        item.save()
    except Exception as e:
        raise SaveError('item', str(e))

    logging.debug(f'item: \n_id:{item._id}\nitem_type:{item.item_type}\nname:{item.name}\ncreated.')

    return jsonify({
        'saved_data': item.response_json(),
        'success': {
            'code': SuccessCode.CREATED.value,
            'message': 'new item created.'
        },
    }), SuccessCode.CREATED.value


@blueprint_items.route('/v1/items/update', methods=['POST'])
def items_update():
    """Update an item.

    /v1/items/update [POST]

    params:
        - _id (str) : Item._id
        - name (str) : 
        - description (str) :
        - price (int) :
        - item_type (int) : ItemType.value
        - lat (float) :
        - lon (float) :
        - store_info_id (str) : StoreInfo._id
    """
 
    logging.info('/v1/items/update [POST]')
    logging.info(request.json)

    # check request header
    if request.headers['Content-Type'] not in ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    _id = request.json.get('_id', type=str)
    name = request.json.get('name', type=str)
    description = request.json.get('description', type=str)
    item_type = request.json.get('item_type', type=int)
    lat = request.json.get('lat', type=float)
    lon = request.json.get('lon', type=float)
    store_info_id = request.json.get('store_info_id', type=str)

    # fetch item
    item = Item.findOne({'_id': _id})
    if not item:
        raise ItemNotFound(_id)

    # check updating parameters
    for key, value in request.json.items():
        if key in ('name'):
            if not Item.validate_name_length(name):
                raise InvalidNameLength(
                    name, Item.__min_name_length__, Item.__max_name_length__)
            item.name = name
        if key in ('description'):
            if not Item.validate_description_length(description):
                raise InvalidDescriptionLength(
                    description, Item.__min_description_length__, Item.__max_description_length__)
            item.description = description
        if key in ('item_type'):
            if item_type in ItemType.values():
                raise InvalidItemType(item_type)
            item.item_type = item_type
        if key in ('lat', 'lon'):
            if isinstance(lat, float) or isinstance(lon, float):
                raise InvalidLatLon(lat, lon)
            item.lat = lat
            item.lon = lon
        if key in ('store_info_id'):
            if not StoreInfo.findOne({'_id': store_info_id}):
                raise StoreInfoNotFound(store_info_id)
            item.store_info_id = store_info_id

    # user_id from context
    user_id = OrganizationMemberSession.user_id()
    if not user_id:
        raise SessionDoesntExistError()

    # fetch user
    organization_member = OrganizationMemberSession.findOne({'_id': user_id})
    if not organization_member:
        raise OrganizationMemberNotFoundError(user_id)
    logging.debug(
        f'organization_member {organization_member._id} found by session_id {user_id}.')

    # update  item
    try:
        item.update()
    except Exception as e:
        raise SaveError('item', str(e))

    logging.debug(f'item {item._id} updated for keys {request.json.keys()}')

    return jsonify({
        'saved_data': item.response_json(),
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'content successfully updated.'
        }
    }), SuccessCode.OK.value


@blueprint_items.route('/v1/items/delete', methods=['POST'])
def items_delete():
    """Delete an item.

    /v1/items/update [POST]

    args:
        - _id (str) : Item._id
    """
    logging.info('/v1/items/delete [POST]')
    logging.info(request.json)

    # check request header
    if request.headers['Content-Type'] not in ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # user_id from  context
    user_id = OrganizationMemberSession.user_id()
    if not user_id:
        raise SessionDoesntExistError()

    # fetch user
    organization_member = OrganizationMemberSession.findOne({'_id': user_id})
    if not organization_member:
        raise OrganizationMemberNotFoundError(user_id)
    logging.debug(
        f'organization_member {organization_member._id} found by session_id {user_id}.')

    # get data
    _id = request.json.get('_id', type=int)

    item = Item.findOne({'_id': item}) 
    logging.info(f'item _id: {item._id} name: {item.name} is trying to be deleted.')

     # update
    try:
        item.delete = True
        item.update()
    except Exception as e:
        raise SaveError('content', str(e))

    logging.debug(f'item {item._id} logically deleted.')

    return jsonify({
        'saved_data': item.response_json(),
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'item successfully deleted.'
        }
    }), SuccessCode.OK.value


@blueprint_items.route('/v1/items/list', methods=['GET'])
def items_list():
    """List an item.

    /v1/items/list [POST]

    """
    logging.info('/v1/items/list [GET]')

    # user_id from  context
    user_id = OrganizationMemberSession.user_id()
    if not user_id:
        raise SessionDoesntExistError()

    # fetch user
    organization_member = OrganizationMemberSession.findOne({'_id': user_id})
    if not organization_member:
        raise OrganizationMemberNotFoundError(user_id)
    logging.debug(
        f'organization_member {organization_member._id} found by session_id {user_id}.')

    # fetch
    items = Item.fetch(organization_member.organization_id, json=True)
    logging.debug(f'{len(items)} items found.')

    return jsonify({
        'saved_data': None,
        'items': items,
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'contents successfully fetched.'
        }
    }), SuccessCode.OK.value

@blueprint_items.route('/v1/items/storeinfo/create', methods=['POST'])
def items_storeinfo_create():
    """Create new store info.

    args:

    """
    pass

@blueprint_items.route('/v1/items/storeinfo/update', methods=['POST'])
def items_storeinfo_update():
    """Update store info.

    args:

    """
    pass

@blueprint_items.route('/v1/items/storeinfo/delete', methods=['POST'])
def items_storeinfo_delete():
    """Delete store info.

    args:

    """
    pass

@blueprint_items.route('/v1/items/storeinfo/list', methods=['GET'])
def items_storeinfo_list():
    """Get store info list.

    args:

    """
    pass

