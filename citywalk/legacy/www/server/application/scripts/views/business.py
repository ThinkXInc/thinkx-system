#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# views/business.py
#

import sys
import json
import logging
import datetime
from bson import ObjectId
from flask import jsonify, Blueprint, request, render_template
from flask_httpauth import HTTPBasicAuth
sys.path.append('../')
from general.config import Config
from models.organization import Organization
from models.organization_member import OrganizationMember
from models.enums.organization_type import OrganizationType
from models.enums.organization_member_role import OrganizationMemberRole
from models.enums.language import Language
from helpers.locale import Locale

auth = HTTPBasicAuth()
basic_auth_items = {
    "<REDACTED>": "<REDACTED>"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_items:
        return basic_auth_items.get(username)
    return None


blueprint_business = Blueprint('business', __name__)

# VIEW Handlers

@blueprint_business.route('/business/top')
def top_handler():
    """Top View.
    """
    return render_template('business/pages/top.html',
        organization=None, organization_member=None)


@blueprint_business.route('/business/home')
def home_handler():
    """Home View.
    """

    # TODO: from cache
    organization = Organization({
        '_id': ObjectId(),
        'name': 'ThinkX Inc.',
        'type': OrganizationType.OTHER_COMPANIES.name,
        'keyname': 'thinkx',
        'zipcode': None,
        'country': 'JP',
        'city': 'Minato',
        'province': 'Tokyo',
        'address1': 'Roppongi 7-7-7',
        'address2': '',
        'tel': '',
    })
    logging.info(organization)
    organization_member = OrganizationMember({
        '_id': ObjectId(),
        'organization_id': 100,
        'first_name': 'Gates',
        'last_name': 'Bill',
        'role': OrganizationMemberRole.ADMIN.name,
        'email': None,
    })
    logging.info(organization_member)
    return render_template('business/pages/home.html',
        organization=organization, organization_member=organization_member)


@blueprint_business.route('/business/signup')
def signup_handler():
    """Signup View.
    
    """
    locale_json = Locale(f'{Config.MESSAGES_ROOT}/signup.json').json()
    lang = Locale.getlang(request)
    print(lang)
    return render_template(
        'business/pages/signup.html',
        organization=None, organization_member=None,
        locale_json=locale_json, lang=lang)


@blueprint_business.route('/business/signin')
def signin_handler():
    """Signin View.
    """
    return render_template('business/signin.html',
        organization=None, organization_member=None)


@blueprint_business.route('/business/settings')
def settings_handler():
    """Settings View.
    """
    logging.info('settings')
    locale_json = Locale(f'{Config.MESSAGES_ROOT}/settings.json').json()
    lang = Locale.getlang(request)

    # TODO: from cache
    organization = Organization({
        '_id': ObjectId(),
        'name': 'ThinkX Inc.',
        'type': OrganizationType.OTHER_COMPANIES.name,
        'keyname': 'thinkx',
        'zipcode': None,
        'country': 'JP',
        'city': 'Minato',
        'province': 'Tokyo',
        'address1': 'Roppongi 7-7-7',
        'address2': 'Tri-Seven Roppongi 8F',
        'lat': 35.6632707,
        'lng': 139.7320854,
        'tel_country_code': '+81',
        'tel': '03-5562-3466',
    })
    logging.info(organization)
    organization_member = OrganizationMember({
        '_id': ObjectId(),
        'organization_id': 100,
        'first_name': 'Gates',
        'last_name': 'Bill',
        'role': OrganizationMemberRole.ADMIN.name,
        'email': None,
    })
    logging.info(organization_member)

    return render_template(
        'business/pages/settings.html',
        organization=organization,
        organization_member=organization_member,
        locale_json=locale_json, lang=lang)


@blueprint_business.route('/business/createguide')
def createguide_handler():
    """Create Guide View.
    """
    logging.info('create guide')
    # TODO: from cache
    organization = Organization({
        '_id': ObjectId(),
        'name': 'ThinkX Inc.',
        'type': OrganizationType.OTHER_COMPANIES.name,
        'keyname': 'thinkx',
        'zipcode': None,
        'country': 'JP',
        'city': 'Minato',
        'province': 'Tokyo',
        'address1': 'Roppongi 7-7-7',
        'address2': '',
        'tel': '',
    })
    logging.info(organization)
    organization_member = OrganizationMember({
        '_id': ObjectId(),
        'organization_id': 100,
        'first_name': 'Gates',
        'last_name': 'Bill',
        'role': OrganizationMemberRole.ADMIN.name,
        'email': None,
    })
    logging.info(organization_member)

    return render_template(
        'business/pages/createguide.html',
        organization=organization,
        organization_member=organization_member)

