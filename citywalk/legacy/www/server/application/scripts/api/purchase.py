#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/user.py
#
#

import sys
sys.path.append('../')
from flask_httpauth import HTTPBasicAuth
from flask import request, jsonify, Blueprint, request
from models.user import User, Plan
from models.error_response import ErrorResponse, ErrorCode
from bson import ObjectId



auth = HTTPBasicAuth()
basic_auth_users = {
    "citywalk": "klawytic"
}

@auth.get_password
def get_password(username):
    if username in basic_auth_users:
        return basic_auth_users.get(username)
    return None

blueprint_purchases = Blueprint('purchases', __name__)

# Errors

class PurchaseAPIInvalidPlanError(Exception):
    def __init__(self, plan):
        self.plan = plan

    def __error_obj__(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.INVALID_PARAMETER.value,
                'reason': ErrorCode.INVALID_PARAMETER.name,
                'message': f'{self.plan} is invalid as plan.'
            }
        )
        return jsonify({'saved_data': None, 'error': error_response.json()}), 400

    def __str__(self):
        return repr(f'{self.plan} is invalid as plan.')


@blueprint_purchases.errorhandler(PurchaseAPIInvalidPlanError)
def purchases_api_invalid_parameter_error(error):
    error_response = error.__error_obj__()
    return error_response


@blueprint_purchases.errorhandler(500)
def internal_server_error(error):
    error_response = ErrorResponse(
        {
            'code': 500,
            'reason': 'InternalServerError',
            'message': 'Internal Server Error'
        }
    )
    return jsonify({'saved_data': None, 'error': error_response.json()}), 500


@blueprint_purchases.errorhandler(502)
def internal_server_error(error):
    error_response = ErrorResponse(
        {
            'code': 502,
            'reason': 'BadGateway',
            'message': 'Bad Gateway'
        }
    )
    return jsonify({'saved_data': None, 'error': error_response.json()}), 502


# Functions

def validate_plan(plan: int):
    if not Plan.validate(plan):
        raise PurchaseAPIInvalidPlanError(plan)

def calc_credit_increment(plan: int):
    """Calculate how many credit should be incremented.
    args:
        - plan: int  # value of Plan
    """
    if not Plan.validate(plan):
        raise PurchaseAPIInvalidPlanError(plan)
    credit = Plan.creditFromIndex(plan)
    print(f'Plan is {Plan.nameFromIndex(plan)}. increment {credit} credits.')
    return credit


# Handlers

@blueprint_purchases.route('/v1/purchases/purchase', methods=['POST'])
@auth.login_required
def purchases_plan():
    """Purchases a plan.
    URI: /v1/purchases/purchase [POST]
    """

    # TODO: get from the request
    user_id = ''
    plan = 1
    discount = 10000
    discount_code = 'XXXXXXXXXXXX'

    # validate
    validate_plan(plan)

    # get user
    user = User.findOne({'user_id': user_id})

    # credit to be incremented
    credit_increment = calc_credit_increment(user.plan)

    # update values
    user.plan = plan
    user.credit += credit_increment
    if discount:
        user.discounts.append(discount)
    if discount_code:
        user.dicount_code = discount_code

    user.save()

    return jsonify({
        'saved_data': user.response_json(),
        'user_id': user_id,
        'success': {
            'code': 201,
            'message': f'plan {Plan.nameFromIndex(plan)} purchased.'
        }
    }), 201
