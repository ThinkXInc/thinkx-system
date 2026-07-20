#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# main.py
#

import logging
from flask import Flask, render_template, request, send_file, send_from_directory, jsonify
from api.users import blueprint_users
from api.organizations import blueprint_organizations
from api.contents import blueprint_contents
from api.items import blueprint_items
from api.histories import blueprint_histories
from api.ratings import blueprint_ratings
from api.addresses import blueprint_addresses
from api.api_response import ErrorResponse, ErrorCode
from views.business import blueprint_business
from general.config import Config
from libcommon.session import RedisSessionInterface, Session
from libcommon.logger import logger

app = Flask(__name__, template_folder='../views/templates')
app.session_interface = RedisSessionInterface()
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # disable HTML cache
app.config['TEMPLATES_AUTO_RELOAD'] = True  # disable HTML cache
lang = 'ja'

# register blueprints
for blueprint in [
    blueprint_users,
    blueprint_organizations,
    blueprint_contents,
    blueprint_items,
    blueprint_ratings,
    blueprint_histories,
    blueprint_business,
    blueprint_addresses
]:
    app.register_blueprint(blueprint)

# all handlers in common
@logger(Config.LOG_FILEPATH)
def before_request():
    pass
app.before_request(before_request)

# basic handlers
@app.route('/')
def top_handler():
    return render_template('index.html')

@app.route('/healthcheck')
def healthcheck():
    return 'Health Check OK!!'

# basic error handlers
@app.errorhandler(400)
def bad_request(error):
    #TODO: html page with error.message (see api_errors.py and api_request.py)
    pass

@app.errorhandler(404)
@blueprint_users.errorhandler(404)
def page_not_found(error):
    error_response = ErrorResponse(
        {
            'code': ErrorCode.NOT_FOUND.value,
            'reason': ErrorCode.NOT_FOUND.name,
            'message': f'{request.url} Not Found.'
        }
    )
    # TODO: return Not Found template.
    return jsonify({'error': error_response.json()}), 404

@app.errorhandler(500)
def internal_server_error(error):
    error_response = ErrorResponse(
        {
            'code': ErrorCode.INTERNAL_SERVER_ERROR.value,
            'reason': ErrorCode.INTERNAL_SERVER_ERROR.name,
            'message': str(error)
        }
    )
    return jsonify({'saved_data': None, 'error': error_response.json()}), \
        ErrorCode.INTERNAL_SERVER_ERROR.value

@app.errorhandler(502)
def internal_server_error(error):
    error_response = ErrorResponse(
        {
            'code': ErrorCode.BAD_GATEWAY.value,
            'reason': ErrorCode.BAD_GATEWAY.name,
            'message': str(error)
        }
    )
    return jsonify({'saved_data': None, 'error': error_response.json()}), \
        ErrorCode.BAD_GATEWAY.value

app.secret_key = '<REDACTED>'

if __name__ == '__main__':
    app.run(
        debug=True,
        secret_key='<REDACTED>',
        max_content_length=70000000
    )
