#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/app.py
#
# /app/version [GET]
# /app/version [POST]
# /app/version/check/<app_type_str> [GET]
#
import uuid

from cerberus import Validator
from flask import Blueprint, jsonify, request
from flask_httpauth import HTTPBasicAuth
from pymongo import DESCENDING

from api.api_logger import ApiLogger
from api.exception.api_errors import ApiErrorDef
from general.cerberus_custom_error_handler import CustomErrorHandler
from general.exceptions import ValidationException
from models.app_version import AppVersion, AppType

api_logger = ApiLogger.get_logger()

auth = HTTPBasicAuth()
basic_auth_users = {
    "beta": "cryptoxanthin"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_users:
        return basic_auth_users.get(username)
    return None


blueprint_apps = Blueprint('app', __name__)


@blueprint_apps.route('/app/version', methods=['GET'])
@auth.login_required
def get_app_version():
    """version retrieve API
    method: GET

    response:
        {
            "ios_version": 1.2.3,
            "android_version": 1.2.3,
        }
    """
    ios = AppVersion.find(query={"app_type": AppType.IOS.value}, sort=[("created", DESCENDING)], limit=1)
    ios_version = ""
    if ios:
        ios_version = ios[0].get("app_version")

    android = AppVersion.find(query={"app_type": AppType.ANDROID.value}, sort=[("created", DESCENDING)],
                              limit=1)
    android_version = ""
    if android:
        android_version = android[0].get("app_version")

    return jsonify({
        'ios_version': ios_version,
        'android_version': android_version,
    })


app_version_validation_def = {
    'app_type': {
        'type': 'string',
        'required': True,
        'regex': f'^({AppType.IOS.name.lower()}|{AppType.ANDROID.name.lower()})$',
    },
    'app_version': {
        'type': 'string',
        'required': True,
    },
}


@blueprint_apps.route('/app/version', methods=['POST'])
@auth.login_required
def post_app_version():
    """version registration API
    method: POST

    request
    {
        app_type: "ios" or "android", :AppType
        app_version: "1.2.3" :str
    }
    response:
        {
            "status": "OK",
            "message": "Success"
        }
    """

    validator = Validator(app_version_validation_def, error_handler=CustomErrorHandler())
    if not validator.validate(request.json):
        raise ValidationException(ApiErrorDef.CERBERUS_VALIDATION_ERROR, [validator.errors])

    app_type = AppType[request.json.get('app_type').upper()]
    app_version = request.json.get('app_version')

    AppVersion(
        {
            "_id": uuid.uuid4(),
            "app_type": app_type.value,
            "app_version": app_version
        }
    ).save()
    return jsonify({
        "status": "OK",
        "message": "Success"
    })


@blueprint_apps.route('/app/version/check/<app_type_str>', methods=['GET'])
@auth.login_required
def app_version_check(app_type_str):
    """ version check API
    method: GET
        /app/version/check/(ios/android)
    request
    {
        app_version: "1.2.3" :str
    }
    response:
        {
            "is_latest_version": false or true,
            "latest_app_version": "1",
            "local_app_version": "0.2.11",
        }
    """
    validator = Validator(app_version_validation_def, error_handler=CustomErrorHandler())

    local_app_version = request.args.get('app_version')
    if not validator.validate({"app_type": app_type_str, "app_version": local_app_version}):
        raise ValidationException(ApiErrorDef.CERBERUS_VALIDATION_ERROR, [validator.errors])
    app_type = AppType[app_type_str.upper()]

    result = AppVersion.find(query={"app_type": app_type.value}, sort=[("created", DESCENDING)], limit=1)
    latest_app_version = ""
    if result:
        latest_app_version = result[0].get("app_version")

    return jsonify({
        "is_latest_version": local_app_version == latest_app_version,
        "local_app_version": local_app_version,
        "latest_app_version": latest_app_version
    })
