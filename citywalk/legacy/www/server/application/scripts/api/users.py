#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/users.py
#
# users API list:
#
#    /v1/users/signup [POST]
#
#         - name (str) :
#         - email (str) :
#         - password (str) :
#
#    /v1/users/signup/confirm [POST]
#
#        - confirmation_code (int) : 
#
#    /v1/users/signin [POST]
#
#        - email (str) :
#        - password (str) :
#
#    /v1/users/update [POST]
#
#       - first_name (str) : (optional)
#       - last_name (str) : (optional)
#       - gender (str) : (optional) Gender model ex) male
#       - nationality (str) : (optional) Country model ISO 3166-1 ex) JA
#       - language (int) : (optional)  # Language ex) 100 ja
#       - zipcode (str) : (optional)
#       - country (str) : (optional) Country model ISO 3166-1 ex) JA
#       - city (str) : (optional)
#       - province (str) : (optional)
#       - address1 (str) : (optional)
#       - address2 (str) : (optional)
#       - tel1 (str) : (optional)
#       - tel2 (str) : (optional)
#       - tel3 (str) : (optional)
#
#    /v1/users/email/update [POST]
#
#        - current_email (str) :
#        - new_email (str) : 
#
#    /v1/users/email/verify [POST]
#
#        - mail_verification_code (int) :
#
#    /v1/users/password/update [POST]
#
#       - previous_password (str) : 
#       - new_password (str) : 
#       - new_password_confirm (str) : 
#
#    /v1/users/password/reset [POST]
#
#        - 
#
#    /v1/users/password/reset/confirm [POST]
#
#        - email (str) :
#        - validation_code (str) : guarantee the one who requested is the owner of the email.
#        - new_password (str) :
#        - new_password_confirm (str) :
#
#   /v1/users/icon/upload [POST]
#
#   /v1/users/exists [POST]
#
#       - email : str
#
#   /v1/users/delete [GET]
#

import sys
import re
import logging
import secrets
from bson import ObjectId
from flask import json, render_template, jsonify, Blueprint, request
from flask_httpauth import HTTPBasicAuth
sys.path.append('../')
from helpers.validator import Validator
from api.api_response import SuccessResponse, ErrorResponse, SuccessCode, \
    ErrorCode
from api.responses.api_errors import InvalidFormatError, ValidationError,\
    RequiredFieldsNotSatisfied, NameTooLongError, \
    SessionDoesntExistError, \
    InvalidUserIDError, InvalidNameError, InvalidEmailFormatError, \
    InvalidPasswordFormatError, PasswordContainsNoAlphabetError,\
    PasswordContainsNoNumberError, \
    ConfirmationPasswordNotCorrespondingError, \
    InvalidZipCodeFormatError, InvalidTelFormatError,\
    InvalidTelCountryCodeFormatError, \
    UserAlreadyExistsError, UserNotFoundError, PasswordIncorrectError, \
    EmailNotCorrespondingError, InvalidContentType, EmailSentFailed, \
    ConfirmationCodeNotCorrespondingError, \
    MailValidationCodeNotCorrespondingError, \
    NewPasswordsNotCorrespondingError, PreviousPasswordIncorrectError, \
    InvalidPasswordResetCodeError, SaveError, \
    InvalidEmailFormatError
from helpers.mail import Mail
from helpers.locale import Locale
from helpers.dateutils import expiration_datetime
from mails.mail_texts import mail_titles, mail_texts
from mails.render_mail import render_signup, render_email_change_success, \
    render_email_change_verification, render_password_change_success, \
    render_password_reset
from models.user import User
from models.enums.gender import Gender
from models.enums.country import Country
from libcommon.cipher import Cipher
from tools.sessions import UserSession


auth = HTTPBasicAuth()
basic_auth_users = {
    "citywalk": "klawytic"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_users:
        return basic_auth_users.get(username)
    return None


blueprint_users = Blueprint('users', __name__)


# ERROR Handlers

@blueprint_users.errorhandler(InvalidUserIDError)
@blueprint_users.errorhandler(InvalidNameError)
@blueprint_users.errorhandler(InvalidEmailFormatError)
@blueprint_users.errorhandler(InvalidPasswordFormatError)
@blueprint_users.errorhandler(InvalidContentType)
@blueprint_users.errorhandler(InvalidFormatError)
@blueprint_users.errorhandler(SessionDoesntExistError)
@blueprint_users.errorhandler(UserAlreadyExistsError)
@blueprint_users.errorhandler(UserNotFoundError)
@blueprint_users.errorhandler(PasswordIncorrectError)
@blueprint_users.errorhandler(EmailNotCorrespondingError)
@blueprint_users.errorhandler(EmailSentFailed)
@blueprint_users.errorhandler(ConfirmationCodeNotCorrespondingError)
@blueprint_users.errorhandler(MailValidationCodeNotCorrespondingError)
@blueprint_users.errorhandler(NewPasswordsNotCorrespondingError)
@blueprint_users.errorhandler(PreviousPasswordIncorrectError)
@blueprint_users.errorhandler(InvalidPasswordResetCodeError)
@blueprint_users.errorhandler(SaveError)
def error_response(error):
    error_reponse = error.__error_obj__()
    return error_reponse


# NOTE: User should not be common with OrganizationMember
# because User registers information interactively.

# request parameters validations
def validate_user_basics(request_json, lang: str) -> list:
    """Validate User paramters (basic informations).

    args:
        - request_json (json) : request.json in handlers
        - lang (str): eg. ja

        first_name = request.json.get('first_name')
        last_name = request.json.get('last_name')
        email = request.json.get('email')
        password = request.json.get('password')
        password_confirm = request.json.get('password_confirm')
 
    returns:
        - errors (list) : list of Error object defined in api_errors.py
    """

    # check submitted values
    errors = []
    # 1. check required fields are satisfied
    required_fields = [
        'first_name', 'last_name', 'email', 'password', 'password_confirm'
    ]
    for key in required_fields:
        if not request_json.get(key):
            errors.append(
                RequiredFieldsNotSatisfied(key, request_json.get(key), lang))
    if len(errors):
        return errors
    # 2. validate each field
    for key, value in request_json.items():
        print(f'{key}: {value}')
        if key in (
                'first_name', 'last_name'):
            if value and (not isinstance(value, str)):
                errors.append(InvalidFormatError(key, value, lang))
        if key in ('first_name', 'last_name'):
            if User.__max_name_length__ < len(value):
                errors.append(
                    NameTooLongError(
                        key, value, User.__max_name_length__, lang))
        if key in ('email'):
            if not re.match(Validator.email_regex, value):
                errors.append(InvalidEmailFormatError(key, value, lang))
        if key in ('password'):
            if not re.match(
                    Validator.password_at_least_one_alphabet_regex, value):
                errors.append(
                    PasswordContainsNoAlphabetError(key, value, lang))
            if not re.match(
                    Validator.password_at_least_one_numeric_regex, value):
                errors.append(
                    PasswordContainsNoNumberError(key, value, lang))
            if not re.match(
                    Validator.password_complete_regex, value):
                errors.append(InvalidPasswordFormatError(key, value, lang))
        if key in ('password_confirm'):
            if request_json.get('password') != value:
                errors.append(
                    ConfirmationPasswordNotCorrespondingError(
                        key, value, lang))

    if len(errors):
        logging.info(f'{len(errors)} errors found in values.')
        return errors


def validate_user_contact(request_json, lang: str) -> list:
    """Validate User paramters (contact infromations).

        zipcode = request.json.get('zipcode')
        city = request.json.get('city')
        province = request.json.get('province')
        address1 = request.json.get('address1')
        address2 = request.json.get('address2')
        tel_country_code = request.json.get('tel_country_code')
        tel = request.json.get('tel')

    args:
        - request_json (json) : request.json in handlers
        - lang (str): eg. ja

    returns:
        - errors (list) : list of Error object defined in api_errors.py
    """

    # check submitted values
    errors = []
    # 1. check required fields are satisfied
    required_fields = [
        'zipcode', 'city', 'province', 'address1',
        'tel_country_code', 'tel',
    ]
    for key in required_fields:
        if not request_json.get(key):
            errors.append(
                RequiredFieldsNotSatisfied(key, request_json.get(key), lang))
    if len(errors):
        return errors
    # 2. validate each field
    for key, value in request_json.items():
        print(f'{key}: {value}')
        if key in (
                'zipcode', 'city', 'province', 'address1', 'address2',
                'tel_country_code', 'tel'):
            if value and (not isinstance(value, str)):
                errors.append(InvalidFormatError(key, value, lang))
        if key in ('zipcode'):
            if not re.match(Validator.zipcode_regex, value):
                errors.append(InvalidZipCodeFormatError(key, value, lang))
        if key in ('tel_country_code'):
            if value not in Country.__dials__.values():
                errors.append(
                    InvalidTelCountryCodeFormatError(key, value, lang))
        if key in ('tel'):
            if not re.match(Validator.tel_regex, value):
                errors.append(InvalidTelFormatError(key, value, lang))

    if len(errors):
        logging.info(f'{len(errors)} errors found in values.')
        return errors
    else:
        return []


# API Handlers

@blueprint_users.route('/v1/users/signup', methods=['POST'])
def users_signup():
    """Signup an account.

    /v1/users/signup [POST]

    params:
        - name : str
        - email : str
        - password : str
        - confirm_password : str
    """
    logging.info('/v1/users/signup [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'], lang)

    # get data
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    email = request.json.get('email')
    password = request.json.get('password')
    password_confirm = request.json.get('password_confirm')
 
    logging.info(f'new user signed up \nname: {organization_name}\
        \nuser: {first_name} {last_name}')

    # validate submitted values
    errors = []
    # basics
    errors = validate_user_basics(request.json)
    logging.debug(errors)
    if len(errors):
        raise ValidationError(errors, lang)

    # encrypt password
    cipher = Cipher()
    password_encrypted = cipher.encrypt(password)

    # check if user already exists
    exists = User.findOne({'email': email})
    if exists:
        raise UserAlreadyExistsError(email, lang)

    # check if new passwords are correctly input
    if password != password_confirm:
        raise NewPasswordsNotCorrespondingError(email, lang)

    # check if password format is valid
    password_validator = Validator.validate_password_format()
    assert password_validator(password) 

    # encrypt password
    cipher = Cipher()
    password_encrypted = cipher.encrypt(password)   

    # generate id
    user_id = User.incrementalId('user_id')
    
    # save user account
    user = User({
        '_id': ObjectId(),
        'user_id': user_id,  # index
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'mail_validation_code': secrets.token_urlsafe(32),
        'password': password_encrypted
    })

    # check if user already exists
    exists = User.findOne({'email': user.email})
    if exists:
        raise UserAlreadyExistsError('email', user.email, lang)

    # save user
    try:
        user.save()
    except Exception as e:
        raise SaveError('organization', str(e), lang)

    logging.debug(
        f'user: \n_id:{user._id}\nuser_id:{user.user_id}\n\
        name:{user.first_name}\nsaved.')

    # start session
    UserSession.start(user_id)

    # send a verification to the new_email
    try:
        Mail.send_mail(
            subject=mail_titles['signup'].en,  # TODO: switch language by user's locale
            text=render_signup(
                user,
                validation_url=f'{Config.HOST_URL}\
                    ?code={user.mail_validation_code}',
                lang='en',
                html=False),
            html=render_signup(
                user,
                validation_url=f'{Config.HOST_URL}\
                    ?code={user.mail_validation_code}',
                lang='en',
                html=True),
            recipient_email=email
        )
    except Exception as e:
        raise EmailSentFailed('email', email, e, lang)
    else:
        return jsonify({
            'saved_data': {
                'user': user.response_json(),
            },
            'success': {
                'code': SuccessCode.CREATED.value,
                'message': 'new user created.'
            },
        }), SuccessCode.CREATED.value


@blueprint_users.route('/v1/users/signup/confirm', methods=['POST'])
def users_signup_confirm():
    """Check confirmation code.

    /v1/users/signup/confirm [POST]

    args:
        - confirmation_code (int) : 
    """
    logging.info('/v1/users/signup/confirm [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    confirmation_code = request.json.get('confirmation_code', type=str)

    # validate parameters
    if not confirmation_code or not re.match(Validator.numeric_only_regex):
        raise InvalidFormatError(confirmation_code, lang)

    # user_id from  context
    user_id = UserSession.user_id()
    if not user_id:
        raise SessionDoesntExistError(lang)

    # fetch user
    user = User.findOne({'user_id': user_id})
    if not user:
        raise UserNotFoundError(user_id, lang)
    logging.debug(f'user {user._id} found by user_id {user_id}.')

    # check confirmation_code
    if user.confirmation_code != confirmation_code:
        raise ConfirmationCodeNotCorrespondingError(confirmation_code, lang)

    # update organization member
    try:
        user.verified = True
        user.update()
    except Exception as e:
        raise SaveError('user', str(e))

    return jsonify({
        'saved_data': user.response_json(),
        'success': {
            'code': SuccessCode.CREATED.value,
            'message': 'user verified.'
        },
    }), SuccessCode.CREATED.value


@blueprint_users.route('/v1/users/signin', methods=['POST'])
def users_signin():
    """Signin to an account.

    /v1/users/signin [POST]

    params:
        - email : str
        - password : str
    """
    logging.info('/v1/users/signin [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'], lang)

    # get data
    email = request.json.get('email')
    password = request.json.get('password')

    # validate parameters
    if not email:
        raise InvalidEmailFormatError(email, lang)
    if not password:
        raise InvalidPasswordFormatError(password, lang)

    # find user
    user = User.findOne({'email': email})

    # if user not found
    if not user:
        raise UserNotFoundError(email, lang)
    logging.debug(f'user {user.user_id} from email {user.email} found.')

    # check password
    cipher = Cipher()
    if not cipher.iscorresponded(password, user.password):
        raise PasswordIncorrectError(email, lang)
    logging.debug(f'password corresponded.')

    # start session
    logging.debug(f'start session.')
    UserSession.start(user.user_id)

    return jsonify({
        'saved_data': None,
        'user_id': user.user_id,
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'Logged in successfully.'
        }
    }), SuccessCode.OK.value


@blueprint_users.route('/v1/users/update', methods=['POST'])
def users_update():
    """Update users properties.

    /v1/users/update [POST]

    params:
       - first_name (str) : (optional)
       - last_name (str) : (optional)
       - gender (str) : (optional) Gender model ex) male
       - nationality (str) : (optional) Country model ISO 3166-1 ex) JA
       - language (int) : (optional)  # Language ex) 100 ja
       - zipcode (str) : (optional)
       - country (str) : (optional) Country model ISO 3166-1 ex) JA
       - city (str) : (optional)
       - province (str) : (optional)
       - address1 (str) : (optional)
       - address2 (str) : (optional)
       - tel1 (str) : (optional)
       - tel2 (str) : (optional)
       - tel3 (str) : (optional)
    """
    logging.info('/v1/users/update [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'], lang)

    # user_id from login session
    user_id = UserSession.user_id()
    if not user_id:
        raise SessionDoesntExistError(lang)

    # fetch user
    user = User.findOne({'user_id': user_id})
    if not user:
        raise UserNotFoundError(user_id, lang)
    logging.debug(f'user {user._id} found by user_id {user_id}.')

    # check parameters
    for key, value in request.json.items():
        if key in ('first_name', 'last_name', 'city',
                   'province', 'address1', 'address2', 'address3'):
            if isinstance(value, str):
                user[key] = value
            else:
                InvalidFormatError(key, value, lang)
        if key in ('zipcode', 'tel1', 'tel2', 'tel3'):
            if re.match(Validator.numeric_only_regex, value):
                user[key] = value
            else:
                raise InvalidFormatError(key, value, lang)
        if key in ('gender'):
            if isinstance(value, str) and value in Gender.itemlist(): 
                user[key] = value
            else:
                raise InvalidFormatError(key, value, lang)
        if key in ('nationality', 'country'):
            if isinstance(value, str) and value in Country.itemlist(): 
                user[key] = value
            else:
                raise InvalidFormatError(key, value, lang)

    # update user
    user.update()
    logging.debug(f'user {user._id} updated for keys {request.json.keys()}')

    return jsonify({
        'saved_data': user.response_json(),
        'user_id': user.user_id,
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'user data successfully updated.'
        }
    }), SuccessCode.OK.value


@blueprint_users.route('/v1/users/email/update', methods=['POST'])
def users_email_update():
    """Update users email.

    1. check if user's input of current email is correct
    2. send a verification to the new email address
    3. return a response

    /v1/users/email/update [POST]

    params:
        - current_email (str) :
        - new_email (str) : 
    """
    logging.info('/v1/users/email/update [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'], lang)

    # get data
    current_email = request.json.get('current_email')
    new_email = request.json.get('new_email')

    # user_id from login session
    user_id = UserSession.user_id()
    if not user_id:
        raise SessionDoesntExistError(lang)

    # fetch user
    user = User.findOne({'user_id': user_id})
    if not user:
        raise UserNotFoundError(user_id, lang)
    logging.debug(f'user {user._id} found by user_id {user_id}.')

    # check if current_email is corresponding
    if not user.email == current_email:
        raise EmailNotCorrespondingError(current_email, lang)

    # check if new_email format is valid
    if not(new_email) or not re.match(Validator.email_regex, new_email):
        raise InvalidEmailFormatError(new_email, lang)

    # validation code
    user.mail_validation_code = secrets.randbits(16)

    # send a verification to the new_email
    try:
        Mail.send_mail(
            subject=mail_titles['email_change_verification'].en,  # TODO: switch language by user's locale
            text=render_email_change_verification(
                user, mail_validation_code=user.mail_validation_code,
                lang='en', html=False),
            html=render_email_change_verification(
                user, mail_validation_code=user.mail_validation_code,
                lang='en', html=True),
            recipient_email=new_email
        )
    except Exception as e:
        raise EmailSentFailed(new_email, e, lang)
    else:
        return jsonify({
            'saved_data': None,
            'user_id': user.user_id,
            'new_email': new_email,
            'success': {
                'code': SuccessCode.OK.value,
                'message': 'updating email validation code sent.'
            }
        }), SuccessCode.OK.value


@blueprint_users.route('/v1/users/email/verify', methods=['POST'])
def users_email_verify():
    """Verify users email.

    /v1/users/email/verify [POST]

    params:
        - mail_verification_code (int) :
    """
    logging.info('/v1/users/email/verify [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'], lang)

    # get data
    mail_verification_code = request.json.get('mail_verification_code')
    new_email = request.json.get('new_email')

    # validate parameters
    if not mail_verification_code or not re.match(
            Validator.numeric_only_regex, mail_verification_code):
        raise InvalidFormatError(mail_verification_code, lang)

    # user_id from  context
    user_id = UserSession.user_id()
    if not user_id:
        raise SessionDoesntExistError(lang)

    # fetch user
    user = User.findOne({'user_id': user_id})
    if not user:
        raise UserNotFoundError(user_id, lang)
    logging.debug(f'user {user._id} found by user_id {user_id}.')

    # check confirmation_code
    if user.mail_verification_code != mail_verification_code:
        raise MailValidationCodeNotCorrespondingError(
            mail_verification_code, lang)
    else:
        previous_email = user.email
        user.email = new_email
        user.update()
        return jsonify({
            'saved_data': user.response_json(),
            'user_id': user_id,
            'previous_email': previous_email,
            'new_email': new_email,
            'success': {
                'code': SuccessCode.OK.value,
                'message': f'user\'s email updated from {previous_email} to {new_email}.'
            },
        }), SuccessCode.OK.value


@blueprint_users.route('/v1/users/password/update', methods=['POST'])
def users_password_update():
    """Update users password.

    /v1/users/password/update [POST]

    1. user inputs
        - previous password
        - new password
        - new password(confirm)

    2. if all 3 are corresponding, update the password.

    params:
       - previous_password (str) : 
       - new_password (str) : 
       - new_password_confirm (str) : 
    """
    logging.info('/v1/users/password/update [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'], lang)

    # get data
    previous_password = request.json.get('previous_password')
    new_password = request.json.get('new_password')
    new_password_confirm = request.json.get('new_password_confirm')

    # user_id from  context
    user_id = UserSession.user_id()
    if not user_id:
        raise SessionDoesntExistError(lang)
    # fetch user
    user = User.findOne({'user_id': user_id})
    if not user:
        raise UserNotFoundError(user_id, lang)
    logging.debug(f'found user {user.email} in session.')

    # check previous password
    cipher = Cipher()
    if not cipher.iscorresponded(previous_password, user.password):
        raise PreviousPasswordIncorrectError(user.email, lang)
    
    # check if new passwords are correctly input
    if new_password != new_password_confirm:
        raise NewPasswordsNotCorrespondingError(user.email, lang)

    # check if password format is valid
    password_validator = Validator.validate_password_format()
    assert password_validator(new_password)

    # send password reset success mail
    try:
        user.password = cipher.encrypt(new_password)
        user.update()

        Mail.send_mail(
            subject=mail_titles['email_change_verification'].en,  # TODO: switch language by user's locale
            text=render_password_change_success(user, lang='en', html=False),
            html=render_password_change_success(user, lang='en', html=True),
            recipient_email=user.email
        )
    except Exception as e:
        raise EmailSentFailed(user.email, e, lang)
    else:
        return jsonify({
            'saved_data': 'password (not returned)',
            'user_id': user.user_id,
            'success': {
                'code': SuccessCode.OK.value,
                'message': 'password was changed successfully.'
            }
        }), SuccessCode.OK.value


@blueprint_users.route('/v1/users/password/reset', methods=['POST'])
def users_login_():
    """Send password reset mail.

    /v1/users/password/reset [POST]

    args:
        - 
    """
    logging.info('/v1/users/password/reset [POST]')

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'], lang)

    # user_id from  context
    user_id = UserSession.user_id()
    if not user_id:
        raise SessionDoesntExistError(lang)
    # fetch user
    user = User.findOne({'user_id': user_id})
    if not user:
        raise UserNotFoundError(user_id, lang)
    logging.debug(f'found user {user.email} in session.')

    # validation_code
    user.password_reset_code = secrets.token_urlsafe()
    user.password_reset_code_expiration = expiration_datetime(after_hours=48)
    user.update()

    # send login recovery mail
    try:
        Mail.send_mail(
            subject=mail_titles['password_reset'].en,  # TODO: switch language by user's locale
            text=render_password_reset(user, lang='en', reset_code=user.password_reset_code, html=False),
            html=render_password_reset(user, lang='en', reset_code=user.password_reset_code, html=True),
            recipient_email=user.email
        )
    except Exception as e:
        raise EmailSentFailed(user.email, e, lang)
    else:
        return jsonify({
            'saved_data': None,
            'user_id': user.user_id,
            'email': user.email,
            'success': {
                'code': SuccessCode.OK.value,
                'message': f'login recovery mail was successfully sent to {user.email}.'
            }
        }), SuccessCode.OK.value


@blueprint_users.route('/v1/users/password/reset/confirm', methods=['POST'])
def users_password_reset():
    """Reset users password.

    /v1/users/password/reset/confirm [POST]

    params:
        - email (str) :
        - password_reset_code (str) : guarantee the one who requested is the owner of the email.
        - new_password (str) :
        - new_password_confirm (str) :
    """
    logging.info('/v1/users/password/reset/confirm [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'], lang)

    # get data
    email = request.json.get('email', str)
    new_password = request.json.get('new_password', str)
    new_password_confirm = request.json.get('new_password_confirm', str)

    # fetch user
    user = User.findOne({'email': email})
    if not user:
        raise UserNotFoundError(email, lang)
    logging.debug(f'found user {user.email} in session.')

    # check reset code validity
    password_reset_code = request.args.get('password_reset_code')
    if user.password_reset_code != password_reset_code:
        raise InvalidPasswordResetCodeError(password_reset_code, lang)

    # check correspondance
    if new_password != new_password_confirm:
        raise NewPasswordsNotCorrespondingError(email, lang)

    # check format
    if not re.match(Validator.password_complete_regex, new_password):
        raise InvalidPasswordFormatError(new_password, lang)

    # update password
    cipher = Cipher()
    user.password = cipher.encrypt(new_password)

    # send password change success mail
    try:
        Mail.send_mail(
            subject=mail_titles['password_change_success'].en,  # TODO: switch language by user's locale
            text=render_password_reset(
                user, password_reset_code=password_reset_code,
                lang=lang, html=False),
            html=render_password_reset(
                user, password_reset_code=password_reset_code,
                lang=lang, html=True),
            recipient_email=user.email
        )
    except Exception as e:
        raise EmailSentFailed(user.email, e, lang)
    else:
        return jsonify({
            'saved_data': None,
            'user_id': user.user_id,
            'email': user.email,
            'success': {
                'code': SuccessCode.OK.value,
                'message': f'password successfully changed for user {user.user_id}.'
            }
        }), SuccessCode.OK.value


@blueprint_users.route('/v1/users/icon/upload', methods=['POST'])
def users_icon_update():
    """Upload users icon.

    /v1/users/icon/upload [POST]

    params:
    """
    logging.info('/v1/users/icon/upload [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'], lang)

    # get data

    pass


@blueprint_users.route('/v1/users/exists', methods=['POST'])
def users_check_exists():
    """Check if the user already exists.

    /v1/users/exists [POST]

    params:
        - email : str
    """

    # locale
    lang = Locale.getlang(request)

    email = request.json.get('email')

    if not email:
        raise InvalidEmailFormatError(email, lang)

    exists = User.findOne({'email': email})
    if exists:
        return jsonify({
            'exists': True,
            'message': f'user from {email} already exists.'
        }), ErrorCode.NOT_FOUND.value
    else:
        return jsonify({
            'exists': False,
            'message': f'user from {email} doesn\'t exist.'
        }), 200