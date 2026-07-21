#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/ratings.py
#
# Rating API:
#  - citywalk
#    [POST] /v1/ratings/citywalk/submit?userId=\(userId)&facilityId=\(facility.id)&rate=\(rate)&comment=\(comment)&timestamp=\(timestamp)
#  - facility
#    [GET] /v1/ratings/facility/<facility_id>/get
#    [POST] /v1/ratings/facility/submit?userId=\(userId)&facilityId=\(facility.id)&rate=\(rate)&comment=\(comment)&timestamp=\(timestamp)
#

import sys
import json
import boto3
from flask_httpauth import HTTPBasicAuth
from flask import request, jsonify, Blueprint, request
from bson import ObjectId
sys.path.append('../')
from models.rating import Rating, RatingType
from api.api_response import ErrorResponse, ErrorCode
import helpers.dateutils as dateutils

client = boto3.client('sqs')
queue_url = "https://sqs.ap-northeast-1.amazonaws.com/027421896362/citywalk-queue-history.fifo"

auth = HTTPBasicAuth()
basic_auth_users = {
    "citywalk": "klawytic"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_users:
        return basic_auth_users.get(username)
    return None


blueprint_ratings = Blueprint('ratings', __name__)


class RatingAPISavingFailError(Exception):
    def __init__(self, message):
        self.message = message

    def __error_obj__(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.INTERNAL_SERVER_ERROR.value,
                'reason': ErrorCode.INTERNAL_SERVER_ERROR.name,
                'message': f'failed to save rating: {message}'
            }
        )
        return jsonify({'saved_data': None, 'error': error_response.json()}), 500

    def __str__(self):
        return repr(f'failed to save rating: {message}')


class RatingAPIGetRatingError(Exception):
    def __init__(self, message):
        self.message = message

    def __error_obj__(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.INTERNAL_SERVER_ERROR.value,
                'reason': ErrorCode.INTERNAL_SERVER_ERROR.name,
                'message': f'failed to get rating: {message}'
            }
        )
        return jsonify({'error': error_response.json()}), 500

    def __str__(self):
        return repr(f'failed to get rating: {message}')



class RatingAPIInvalidIdentifierError(Exception):
    def __init__(self, user_id):
        self.user_id = user_id

    def __error_obj__(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.INVALID_PARAMETER.value,
                'reason': ErrorCode.INVALID_PARAMETER.name,
                'message': f'{self.user_id} is invalid as user_id.'
            }
        )
        return jsonify({'saved_data': None, 'error': error_response.json()}), 400

    def __str__(self):
        return repr(f'{self.user_id} is invalid as user_id.')


class RatingAPIInvalidTimestampError(Exception):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def __error_obj__(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.INVALID_PARAMETER.value,
                'reason': ErrorCode.INVALID_PARAMETER.name,
                'message': f'{self.timestamp} is invalid as timestamp.'
            }
        )
        return jsonify({'saved_data': None, 'error': error_response.json()}), 400

    def __str__(self):
        return repr(f'{self.timestamp} is invalid as timestamp.')


class RatingAPIInvalidFacilityIDError(Exception):
    def __init__(self, facility_id):
        self.facility_id = facility_id

    def __error_obj__(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.INVALID_PARAMETER.value,
                'reason': ErrorCode.INVALID_PARAMETER.name,
                'message': f'{self.facility_id} is invalid as facility_id.'
            }
        )
        return jsonify({'saved_data': None, 'error': error_response.json()}), 400

    def __str__(self):
        return repr(f'{self.facility_id} is invalid as facility_id.')


class RatingAPIInvalidRateError(Exception):
    def __init__(self, rate):
        self.rate = rate

    def __error_obj__(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.INVALID_PARAMETER.value,
                'reason': ErrorCode.INVALID_PARAMETER.name,
                'message': f'{self.rate} is invalid as rate.'
            }
        )
        return jsonify({'saved_data': None, 'error': error_response.json()}), 400

    def __str__(self):
        return repr(f'{self.rate} is invalid as rate.')


@blueprint_ratings.errorhandler(RatingAPIInvalidIdentifierError)
@blueprint_ratings.errorhandler(RatingAPIInvalidTimestampError)
@blueprint_ratings.errorhandler(RatingAPIInvalidFacilityIDError)
@blueprint_ratings.errorhandler(RatingAPIInvalidRateError)
@blueprint_ratings.errorhandler(RatingAPISavingFailError)
@blueprint_ratings.errorhandler(RatingAPIGetRatingError)
@blueprint_ratings.errorhandler(dateutils.InvalidISOFormatError)
def rating_api_invalid_parameter_error(error):
    error_response = error.__error_obj__()
    return error_response


@blueprint_ratings.errorhandler(500)
def internal_server_error(error):
    error_response = ErrorResponse(
        {
            'code': 500,
            'reason': 'InternalServerError',
            'message': 'Internal Server Error'
        }
    )
    return jsonify({'saved_data': None, 'error': error_response.json()}), 500


@blueprint_ratings.errorhandler(502)
def internal_server_error(error):
    error_response = ErrorResponse(
        {
            'code': 502,
            'reason': 'BadGateway',
            'message': 'Bad Gateway'
        }
    )
    return jsonify({'saved_data': None, 'error': error_response.json()}), 502


@blueprint_ratings.route('/v1/ratings/facility/<facility_id>/get', methods=['GET'])
@auth.login_required
def api_get_rating_facility(facility_id):
    """Get Rating for a facility.

    parameters:
        - facilityId: str
    returns:
        - facility_id: str
        - rate_count: int
        - rate_average: float
    """
    facility_id = str(facility_id)
    try:
        result = Rating.facility_rating(facility_id)
    except Exception as e:
        raise RatingAPIGetRatingError(e)
    else:
        return jsonify(result), 201


@blueprint_ratings.route('/v1/ratings/facility/submit', methods=['POST'])
@auth.login_required
def api_submit_rating_facility():
    """Submit Rating for a facility.

    parameters:
        - userId: str
        - facilityId: str
        - rate: int
        - comment: str
        - timestamp: str
    """

    user_id = request.args.get('userId', type=str)
    facility_id = request.args.get('facilityId', type=str)
    rate = request.args.get('rate', type=int)
    comment = request.args.get('comment', type=str)
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp', type=str))

    # TODO: use logger.debug()
    print(
        f"/v1/ratings/facility/submit received facility_id {facility_id} rate {rate} comment {comment} [{utc_date}] user_id: {user_id}")

    if user_id is None:
        raise RatingAPIInvalidIdentifierError(user_id)
    if facility_id is None:
        raise RatingAPIInvalidfacilityIdError(facility_id)
    if utc_date is None:
        raise RatingAPIInvalidTimestampError(utc_date)
    if (rate is None) or (isinstance(rate, int) and rate == 0):
        raise RatingAPIInvalidRateError(rate)

    rating = Rating({
        '_id': ObjectId(),
        'user_id': user_id,
        'facility_id': facility_id,
        'rating_type': RatingType.FACILITY.value,
        'rate': rate,
        'comment': comment,
        'utc_date': utc_date
    })
    try:
        rating.save()
    except Exception as e:
        raise RatingAPISavingFailError(e)
    else:
        return jsonify({'status': 'submit rating success.', 'saved_data': rating.response_json()}), 201


@blueprint_ratings.route('/v1/ratings/citywalk/submit', methods=['POST'])
@auth.login_required
def api_submit_rating_citywalk():
    """Submit Rating for citywalk.

    parameters:
        - userId: str
        - rate: int
        - comment: str
        - timestamp: str
    """

    user_id = request.args.get('userId', type=str)
    rate = request.args.get('rate', type=int)
    comment = request.args.get('comment', type=str)
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp', type=str))

    # TODO: use logger.debug()
    print(
        f"/v1/ratings/citywalk/submit received rate {rate} comment {comment} [{utc_date}] user_id: {user_id}")

    if user_id is None:
        raise RatingAPIInvalidIdentifierError(user_id)
    if utc_date is None:
        raise RatingAPIInvalidTimestampError(utc_date)
    if (rate is None) or (isinstance(rate, int) and rate == 0):
        raise RatingAPIInvalidRateError(rate)

    rating = Rating({
        '_id': ObjectId(),
        'user_id': user_id,
        'rate': rate,
        'rating_type': RatingType.CITYWALK.value,
        'comment': comment,
        'utc_date': utc_date
    })
    try:
        rating.save()
    except Exception as e:
        raise RatingAPISavingFailError(e)
    else:
        return jsonify({'status': 'submit rating success.', 'saved_data': rating.response_json()}), 201
