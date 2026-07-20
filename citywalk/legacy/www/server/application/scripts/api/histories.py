#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/histories.py
#
# History API:
#  /v1/histories/location/gps?userId=\(userId)&facilityId=\(facility.id)&lat=\(lat)&lon=\(lon)&timestamp=\(timestamp)
#  /v1/histories/location/hgps?userId=\(userId)&facilityId=\(facility.id)&hgx=\(hgx)&hgy=\(hgy)&timestamp=\(timestamp)
#  /v1/histories/location/pathnet?userId=\(userId)&facilityId=\(facility.id)&px=\(px)&py=\(py)&timestamp=\(timestamp)
#  /v1/histories/app/launch?userId=\(userId)&timestamp=\(timestamp)
#  /v1/histories/app/enterbackground?userId=\(userId)&timestamp=\(timestamp)
#  /v1/histories/facilitypanel/selected?userId=\(userId)&facilityId=\(facilityId)&timestamp=\(timestamp)
#  /v1/histories/guide/checkin?userId=\(userId)&facilityId=\(facility.id)&checkInPanelId=\(checkInPanel.id)&timestamp=\(timestamp)
#  /v1/histories/guide/start?userId=\(userId)&facilityId=\(facility.id)&timestamp=\(timestamp)
#  /v1/histories/guide/finish?userId=\(userId)&facilityId=\(facility.id)&timestamp=\(timestamp)
#  /v1/histories/question/answer?userId=\(userId)&facilityId=\(facility.id)&questionId=\(question.id)&timestamp=\(timestamp)
#  /v1/histories/audiocontent/play?userId=\(userId)&facilityId=\(facility.id)&audioContentuserId=\(audioContent.id)&timestamp=\(timestamp)
#  /v1/histories/audiocontent/stop?userId=\(userId)&facilityId=\(facility.id)&audioContentuserId=\(audioContent.id)&playbackRate=\(playbackRate)&timestamp=\(timestamp)
#  /v1/histories/audiocontent/finish?userId=\(userId)&facilityId=\(facility.id)&audioContentuserId=\(audioContent.id)&timestamp=\(timestamp)


import sys
sys.path.append('../')
from flask_httpauth import HTTPBasicAuth
from flask import request, jsonify, Blueprint, request
from models.history import History, ActionType
from api.api_response import ErrorResponse, ErrorCode
from api.responses.api_errors import InvalidUserIDError, InvalidTimestampError, InvalidLatLonError, \
    InvalidXYError, InvalidFacilityIDError, InvalidQuestionIDError, InvalidPlaybackRateError, \
    InvalidAnswerError, InvalidAudioContentIDError, InvalidCheckInPanelIDError
from bson import ObjectId
import boto3
import json
import helpers.dateutils as dateutils
import uuid
import logging

client = boto3.client('sqs')
queue_url = "https://sqs.ap-northeast-1.amazonaws.com/027421896362/citywalk-queue-history"

auth = HTTPBasicAuth()
basic_auth_users = {
    "citywalk": "klawytic"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_users:
        return basic_auth_users.get(username)
    return None


blueprint_histories = Blueprint('histories', __name__)


@blueprint_histories.errorhandler(InvalidUserIDError)
@blueprint_histories.errorhandler(InvalidTimestampError)
@blueprint_histories.errorhandler(InvalidAudioContentIDError)
@blueprint_histories.errorhandler(InvalidCheckInPanelIDError)
@blueprint_histories.errorhandler(InvalidFacilityIDError)
@blueprint_histories.errorhandler(InvalidLatLonError)
@blueprint_histories.errorhandler(InvalidQuestionIDError)
@blueprint_histories.errorhandler(InvalidXYError)
@blueprint_histories.errorhandler(dateutils.InvalidISOFormatError)
def history_api_invalid_parameter_error(error):
    error_response = error.__error_obj__()
    return error_response


@blueprint_histories.errorhandler(500)
def internal_server_error(error):
    error_response = ErrorResponse(
        {
            'code': 500,
            'reason': 'InternalServerError',
            'message': 'Internal Server Error'
        }
    )
    return jsonify({'saved_data': None, 'error': error_response.json()}), 500


@blueprint_histories.errorhandler(502)
def internal_server_error(error):
    error_response = ErrorResponse(
        {
            'code': 502,
            'reason': 'BadGateway',
            'message': 'Bad Gateway'
        }
    )
    return jsonify({'saved_data': None, 'error': error_response.json()}), 502


@blueprint_histories.route('/v1/histories/location/gps', methods=['POST'])
@auth.login_required
def api_history_location_gps():
    """Save history UPDATE_GPS_LOCATION action.

    URI: /v1/histories/location/gps?userId=\(userId)&facilityId=\(facility.id)&lat=\(lat)&lon=\(lon)&timestamp=\(timestamp)
    """

    user_id = request.args.get('userId')
    timestamp = request.args.get('timestamp')
    facility_id = request.args.get('facilityId')
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    # TODO: use logger.debug()
    logging.debug(
        f"/v1/histories/location/gps received facility_id {facility_id} (lat {lat}, lon {lon}) [{timestamp}] user_id: {user_id}")

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if timestamp is None:
        raise InvalidTimestampError(timestamp)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)
    if lat is None or lon is None:
        raise InvalidLatLonError(lat, lon)

    history = {
        'user_id': user_id,
        'action_type': ActionType.UPDATE_GPS_LOCATION.value,
        'timestamp': timestamp,
        'facility_id': facility_id,
        'lat': lat,
        'lon': lon,
    }
    message_group_id = 'citywalk-history-' + str(uuid.uuid4())
    sent_message = client.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps(history))
    return jsonify({
        'success': {
            'code': 201,
            'message': 'successfully saved location history.'
        },
        'saved_data': sent_message
    }), 201


@ blueprint_histories.route('/v1/histories/location/hgps', methods=['POST'])
@ auth.login_required
def api_history_location_hgps():
    """Save history UPDATE_HGPS_LOCATION action.

    URI: /v1/histories/location/hgps?userId=\(userId)&facilityId=\(facility.id)&hgx=\(hgx)&hgy=\(hgy)&timestamp=\(timestamp)

    """

    user_id = request.args.get('userId')
    timestamp = request.args.get('timestamp')
    facility_id = request.args.get('facilityId')
    hgx = request.args.get('hgx')
    hgy = request.args.get('hgy')

    # TODO: use logger.debug()
    print(
        f"/v1/histories/location/gps received facility_id {facility_id} (hgx {hgx}, hgy {hgy}) [{timestamp}]")

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if timestamp is None:
        raise InvalidTimestampError(timestamp)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)
    if hgx is None or hgy is None:
        raise InvalidXYError(hgx, hgy)

    history = {
        'user_id': user_id,
        'action_type': ActionType.UPDATE_HGPS_LOCATION.value,
        'timestamp': timestamp,
        'facility_id': facility_id,
        'hgx': hgx,
        'hgy': hgy
    }
    message_group_id = 'citywalk-history-' + str(uuid.uuid4())
    sent_message = client.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps(history))
    return jsonify({
        'success': {
            'code': 201,
            'message': 'successfully saved location history.'
        },
        'saved_data': sent_message
    }), 201


@ blueprint_histories.route('/v1/histories/location/pathnet', methods=['POST'])
@ auth.login_required
def api_history_location_pathnet():
    """Save history UPDATE_PATHNET_LOCATION action.

    URI: /v1/histories/location/pathnet?userId=\(userId)&FacilityID=\(facility.id)&px=\(px)&py=\(py)&timestamp=\(timestamp)

    """

    user_id = request.args.get('userId')
    timestamp = request.args.get('timestamp')
    facility_id = request.args.get('FacilityID')
    px = request.args.get('hgx')
    py = request.args.get('hgy')

    # TODO: use logger.debug()
    print(
        f"/v1/histories/location/pathnet received facility_id {facility_id} (px {px}, py {py}) [{timestamp}]")

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if timestamp is None:
        raise InvalidTimestampError(timestamp)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)
    if hgx is None or hgy is None:
        raise InvalidXYError(px, py)

    history = {
        'user_id': user_id,
        'action_type': ActionType.UPDATE_PATHNET_LOCATION.value,
        'timestamp': timestamp,
        'facility_id': facility_id,
        'px': px,
        'py': py,
    }
    message_group_id = 'citywalk-history-' + str(uuid.uuid4())
    sent_message = client.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps(history))
    return jsonify({
        'success': {
            'code': 201,
            'message': 'successfully saved location history.'
        },
        'saved_data': sent_message
    }), 201


@blueprint_histories.route('/v1/histories/app/launch', methods=['POST'])
@auth.login_required
def api_history_applaunch():
    """Save history DidAppLaunch action.

    URI: /history/app/launch?userId=\(userId)&timestamp=\(timestamp)

    """
    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    history = History(
        {'_id': ObjectId(), 'action_type': ActionType.LAUNCH_APP.value, 'utc_date': utc_date, 'user_id': user_id})
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201

    # NOTE: SQSの受信サーバーに送る場合，最終的にConsumerがMongoBaseで保存できるようJSONの形式を変えずに送るか,
    # Redisを用いる場合は元のMongoBase(JSON)形式を保持するようredisのデータ型を用意し格納する必要がある．
    # この場合RedisBaseというMongoBaseに似たORMがあるのでそれを用いる．


@blueprint_histories.route('/v1/histories/app/enterbackground', methods=['POST'])
@auth.login_required
def api_history_enterbackground():
    """Save history DidEnterBackground action.

    URI: /history/app/enterbackground?userId=\(userId)&timestamp=\(timestamp)
    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp',))

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)

    history = History(
        {'_id': ObjectId(), 'action_type': ActionType.ENTER_BACKGROUND.value, 'user_id': user_id, 'utc_date': utc_date})
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/app/terminate', methods=['POST'])
@auth.login_required
def api_history_terminate():
    """Save history Terminate App action.

    URI: /history/app/terminate?userId=\(userId)&timestamp=\(timestamp)
    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)

    history = History(
        {'_id': ObjectId(), 'action_type': ActionType.TERMINATE_APP.value, 'user_id': user_id, 'utc_date': utc_date})
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/facilitypanel/selected', methods=['POST'])
@auth.login_required
def api_history_tapfacility():
    """Save history DidTapFacility action.

    URI: /history/facilitypanel/selected?userId=\(userId)&facilityuserId=\(FacilityID)&timestamp=\(timestamp)
    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    facility_id = request.args.get('FacilityID')

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)

    history = History({'_id': ObjectId(), 'action_type': ActionType.TAP_FACILITY.value, 'user_id': user_id,
                       'utc_date': utc_date, 'facility_id': facility_id})
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/guide/checkin', methods=['POST'])
@auth.login_required
def api_history_checkin():
    """Save history DidCheckIn action.

    URI: /v1/histories/guide/checkin?userId=\(userId)&FacilityID=\(facility.id)&checkInPanelId=\(checkInPanel.id)&timestamp=\(timestamp)
    """

    user_id = request.args.get('id')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    facility_id = request.args.get('FacilityID')
    checkinpanel_id = request.args.get('checkInPanelid')

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)
    if checkinpanel_id is None:
        raise InvalidCheckInPanelIDError(checkinpanel_id)

    history = History(
        {
            '_id': ObjectId(),
            'action_type': ActionType.CHECKIN.value,
            'utc_date': utc_date,
            'facility_id': facility_id,
            'checkinpanel_id': checkinpanel_id
        })
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/guide/start', methods=['POST'])
@auth.login_required
def api_history_startguide():
    """Save history DidStartGuide action.

    URI: /v1/histories/guide/start?userId=\(userId)&FacilityID=\(facility.id)&timestamp=\(timestamp)
    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    facility_id = request.args.get('FacilityID')

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)

    history = History(
        {
            '_id': ObjectId(),
            'action_type': ActionType.START_GUIDE.value,
            'user_id': user_id,
            'utc_date': utc_date,
            'facility_id': facility_id,
        })
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/guide/stop', methods=['POST'])
@auth.login_required
def api_history_stopguide():
    """Save history DidStopGuide action.

    URI: /v1/histories/guide/stop?userId=\(userId)&FacilityID=\(facility.id)&timestamp=\(timestamp)
    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    facility_id = request.args.get('FacilityID')

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)

    history = History(
        {
            '_id': ObjectId(),
            'action_type': ActionType.STOP_GUIDE.value,
            'user_id': user_id,
            'utc_date': utc_date,
            'facility_id': facility_id,
        })
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/guide/finish', methods=['POST'])
@auth.login_required
def api_history_finishguide():
    """Save history DidFinishGuide action.

    URI: /v1/histories/guide/finish?userId=\(userId)&FacilityID=\(facility.id)&timestamp=\(timestamp)

    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    facility_id = request.args.get('FacilityID')

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)

    history = History(
        {
            '_id': ObjectId(),
            'action_type': ActionType.FINISH_GUIDE.value,
            'user_id': user_id,
            'utc_date': utc_date,
            'facility_id': facility_id,
        })
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/question/answer', methods=['POST'])
@auth.login_required
def api_history_answerquestion():
    """Save history DidAnswerQuestion action.

    URI: /v1/histories/question/answer?userId=\(userId)&FacilityID=\(facility.id)&questionId=\(question.id)&answer=\(answer)&timestamp=\(timestamp)
    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    facility_id = request.args.get('FacilityID')
    question_id = request.args.get('questionId')
    answer = request.args.get('answer')

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)
    if question_id is None:
        raise InvalidQuestionIDError(question_id)
    if answer is None:
        raise InvalidAnswerError(question_id)


    history = History(
        {
            '_id': ObjectId(),
            'action_type': ActionType.ANSWER_QUESTIONS.value,
            'user_id': user_id,
            'utc_date': utc_date,
            'facility_id': facility_id,
            'question_id': question_id
        })
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/audiocontent/play', methods=['POST'])
@auth.login_required
def api_history_playaudiocontent():
    """Save history DidPlayAudioContent action.

    URI: /v1/histories/audiocontent/play?userId=\(userId)&facilityuserId=\(facility.id)&audioContentuserId=\(audioContent.id)&timestamp=\(timestamp)

    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    facility_id = request.args.get('FacilityID')
    audio_content_id = request.args.get('audioContentID')

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)
    if audio_content_id is None:
        raise InvalidAudioContentIDError(audio_content_id)

    history = History(
        {
            '_id': ObjectId(),
            'action_type': ActionType.PLAY_AUDIO_CONTENT.value,
            'user_id': user_id,
            'utc_date': utc_date,
            'facility_id': facility_id,
            'audio_content_id': audio_content_id
        })
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/audiocontent/stop', methods=['POST'])
@auth.login_required
def api_history_stopaudiocontent():
    """Save history DidStopAudioContent action.

    URI: /v1/histories/audiocontent/stop?userId=\(userId)&facilityuserId=\(facility.id)&audioContentuserId=\(audioContent.id)&playbackRate=\(playbackRate)&timestamp=\(timestamp)

    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    facility_id = request.args.get('FacilityID')
    audio_content_id = request.args.get('audioContentID')
    playback_rate = request.args.get('playbackRate')

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)
    if audio_content_id is None:
        raise InvalidAudioContentIDError(audio_content_id)
    if playback_rate is None:
        raise InvalidPlaybackRateError(playback_rate)

    history = History(
        {
            '_id': ObjectId(),
            'action_type': ActionType.STOP_AUDIO_CONTENT.value,
            'user_id': user_id,
            'utc_date': utc_date,
            'facility_id': facility_id,
            'audiocontent_id': audio_content_id
        })
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201


@blueprint_histories.route('/v1/histories/audiocontent/finish', methods=['POST'])
@auth.login_required
def api_history_finishaudiocontent():
    """Save history DidFinishAudioContent action.

    URI: /v1/histories/audiocontent/finish?userId=\(userId)&facilityuserId=\(facility.id)&audioContentuserId=\(audioContent.id)&timestamp=\(timestamp)

    """

    user_id = request.args.get('userId')
    utc_date = dateutils.iso8061_to_datetime(
        request.args.get('timestamp'))
    facility_id = request.args.get('FacilityID')
    audio_content_id = request.args.get('audioContentID')

    if user_id is None:
        raise InvalidUserIDError(user_id)
    if utc_date is None:
        raise InvalidTimestampError(utc_date)
    if facility_id is None:
        raise InvalidFacilityIDError(facility_id)
    if audio_content_id is None:
        raise InvalidAudioContentIDError(audio_content_id)

    history = History(
        {
            '_id': ObjectId(),
            'action_type': ActionType.FINISH_AUDIO_CONTENT.value,
            'user_id': user_id,
            'utc_date': utc_date,
            'facility_id': facility_id,
            'audiocontent_id': audio_content_id
        })
    save_data = history.save()
    return jsonify({'status': 'saved history success.', 'saved_data': history.response_json()}), 201
