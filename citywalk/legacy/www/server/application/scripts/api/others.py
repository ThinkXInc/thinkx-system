#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/others.py
#
# /standard/intake [GET]
#

from cerberus import Validator
from flask import request, jsonify, Blueprint
from flask_httpauth import HTTPBasicAuth

from api.exception.api_errors import ApiErrorDef
from general.cerberus_custom_error_handler import CustomErrorHandler
from general.exceptions import ValidationException
from models.age import Age
from models.health_goals import HealthGoalsNutrients, HealthGoals
from models.nutrient import Nutrient
from models.sex import Sex
from models.standard import Standard


auth = HTTPBasicAuth()
basic_auth_users = {
    "beta": "cryptoxanthin"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_users:
        return basic_auth_users.get(username)
    return None


blueprint_others = Blueprint('others', __name__)

