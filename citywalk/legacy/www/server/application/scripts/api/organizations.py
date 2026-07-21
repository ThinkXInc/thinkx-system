#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/organizations.py
#
# users API list:
#
#    /organizations/signup [POST]
#
#        - organization_name (str) :
#        - organization_type (int) : OrganizationType
#        - business_description (string) :
#        - zipcode (str) :
#        - country (str) : Country.name
#        - city (str) :
#        - province (str) :
#        - address1 (str) :
#        - address2 (str) :
#        - tel_country_code (str) :
#        - tel (str) :
#        - first_name (str) :
#        - last_name (str) :
#        - email (str) :
#        - password (str) :
#        - password_confirm (str) :
# 
#    /organizations/signup/confirm [POST]
#
#        - confirmation_code (int) : 
# 
#    /organizations/signin [POST]
#
#        - email (str) :
#        - password (str) :
#
#    /organizations/organization/update [POST]
#
#       - name (str) : (optional)
#       - type (int) : (optional) OrganiztionType.value
#       - country (str) : (optional) Country.name
#       - zipcode (str) : (optional)
#       - city (str) : (optional)
#       - province (str) : (optional)
#       - address1 (str) : (optional)
#       - address2 (str) : (optional)
#       - tel1 (str) : (optional)
#       - tel2 (str) : (optional)
#       - tel3 (str) : (optional)
# 
#    /organizations/member/update [POST]
#
#       - first_name (str) : (optional)
#       - last_name (str) : (optional)
#       - email (str) : (optional)
#       - country (str) : (optional) Country.name
#       - zipcode (str) : (optional)
#       - city (str) : (optional)
#       - province (str) : (optional)
#       - address1 (str) : (optional)
#       - address2 (str) : (optional)
#       - tel1 (str) : (optional)
#       - tel2 (str) : (optional)
#       - tel3 (str) : (optional)
# 
#    /organizations/member/role/update [POST]
#
#        - target_member_id (str) : OrganizationMember._id
#        - role (int) : (optional) OrganizationMemberRole.value
#
#    /organizations/email/update [POST]
#
#        - current_email (str) :
#        - new_email (str) : 
#
#    /organizations/email/verify [POST]
#
#        - mail_verification_code (int) :
#
#    /organizations/password/update [POST]
#
#       - previous_password (str) : 
#       - new_password (str) : 
#       - new_password_confirm (str) : 
#
#    /organizations/password/reset [POST]
#
#        - 
#
#    /organizations/password/reset/confirm [POST]
#
#        - email (str) :
#        - validation_code (str) : guarantee the one who requested is the owner of the email.
#        - new_password (str) :
#        - new_password_confirm (str) :
#
#   /organizations/icon/upload [POST]
#
#   /organizations/exists [POST]
#
#       - email : str
#
#   /organizations/delete [GET]
#

import sys
import re
import logging
import secrets
from bson import ObjectId
from flask import render_template, jsonify, Blueprint, request
from flask_httpauth import HTTPBasicAuth
from general.config import Config
from tools.sessions import OrganizationMemberSession
from models.enums.country import Country
from models.enums.organization_type import OrganizationType
from models.organization import Organization
from models.organization_member import OrganizationMember, OrganizationMemberRole
sys.path.append('../')
from helpers.validator import Validator
from api.api_response import SuccessResponse, ErrorResponse, SuccessCode, \
    ErrorCode
from api.responses.api_errors import ValidationError, InvalidFormatError, \
    SessionDoesntExistError, \
    InvalidEmailFormatError, InvalidPasswordFormatError, InvalidNameError, \
    UserAlreadyExistsError, UserNotFoundError, PasswordIncorrectError, \
    EmailNotCorrespondingError, InvalidContentType, EmailSentFailed, \
    ConfirmationCodeNotCorrespondingError, \
    MailValidationCodeNotCorrespondingError, \
    NewPasswordsNotCorrespondingError, PreviousPasswordIncorrectError, \
    InvalidPasswordResetCodeError, InvalidOrganizationTypeError, SaveError, \
    OrganizationMemberCannotResignAdminRoleError, \
    OrganizationMemberPermissionDeniedError, \
    OrganizationNotFoundError, TargetMemberNotFoundError, \
    OrganizationKeynameAlreadyExistError, OrganizationMemberNotFoundError, \
    NameTooLongError, InvalidZipCodeFormatError, InvalidTelFormatError, \
    InvalidLatLngFormatError, \
    InvalidTelCountryCodeFormatError, PasswordContainsNoAlphabetError, \
    PasswordContainsNoNumberError, \
    RequiredFieldsNotSatisfied, ConfirmationPasswordNotCorrespondingError, \
    InvalidCountryError
from api.responses.api_successes import OK, CREATED
from helpers.mail import Mail
from helpers.locale import Locale
from helpers.dateutils import expiration_datetime
from mails.mail_texts import mail_titles, mail_texts
from mails.render_mail import render_signup_organization, \
    render_password_reset_organization_member, \
    render_password_change_success_organization_member, \
    render_password_reset_organization_member, \
    render_email_change_verification_organization_member
from libcommon.cipher import Cipher


auth = HTTPBasicAuth()
basic_auth_organizations = {
    "citywalk": "klawytic"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_organizations:
        return basic_auth_organizations.get(username)
    return None


blueprint_organizations = Blueprint('organizations', __name__)


# ERROR Handlers

@blueprint_organizations.errorhandler(ValidationError)
@blueprint_organizations.errorhandler(SessionDoesntExistError)
@blueprint_organizations.errorhandler(InvalidPasswordFormatError)
@blueprint_organizations.errorhandler(UserAlreadyExistsError)
@blueprint_organizations.errorhandler(UserNotFoundError)
@blueprint_organizations.errorhandler(PasswordIncorrectError)
@blueprint_organizations.errorhandler(EmailNotCorrespondingError)
@blueprint_organizations.errorhandler(InvalidContentType)
@blueprint_organizations.errorhandler(EmailSentFailed)
@blueprint_organizations.errorhandler(ConfirmationCodeNotCorrespondingError)
@blueprint_organizations.errorhandler(MailValidationCodeNotCorrespondingError)
@blueprint_organizations.errorhandler(NewPasswordsNotCorrespondingError)
@blueprint_organizations.errorhandler(InvalidPasswordResetCodeError)
@blueprint_organizations.errorhandler(SaveError)
@blueprint_organizations.errorhandler(OrganizationMemberCannotResignAdminRoleError)
@blueprint_organizations.errorhandler(TargetMemberNotFoundError)
@blueprint_organizations.errorhandler(OrganizationKeynameAlreadyExistError)
@blueprint_organizations.errorhandler(OrganizationMemberNotFoundError)
def error_response(error):
    error_reponse = error.__error_obj__()
    return error_reponse


# request parameters validations
def validate_organization_basics(request_json, lang: str) -> list:
    """Validate Organization paramters (Page 1 in signup).

        # Page 1
        organization_name = request_json.get('organization_name')
        organization_type = request_json.get('organization_type')
        business_description = request_json.get('business_description')
        country = request_json.get('country')

    args:
        - request_json (json) : request.json in handlers
        - lang (str) : language to be output

    returns:
        - errors (list) : list of Error object defined in api_errors.py
    """

    # check submitted values
    errors = []
    # 1. check required fields are satisfied
    required_fields = [
        'organization_name', 'organization_type', 'business_description',
        'country']
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
                'organization_name', 'business_description'):
            if value and (not isinstance(value, str)):
                errors.append(InvalidFormatError(key, value, lang))
        if key in ['organization_name']:
            if Organization.__max_name_length__ < len(value):
                errors.append(
                    NameTooLongError(
                        key, value, Organization.__max_name_length__))
        if key in ['organization_type']:
            if value not in OrganizationType.values():
                errors.append(InvalidOrganizationTypeError(key, value, lang))
        if key in ['country']:
            if value not in Country.itemlist():
                errors.append(InvalidCountryError(key, value, lang))

    if len(errors):
        logging.info(f'{len(errors)} errors found in values.')
        return errors


def validate_organization_contact(request_json, lang: str) -> list:
    """Validate Organization paramters (Page 2 in signup).

        # Page 2
        zipcode = request.json.get('zipcode')
        city = request.json.get('city')
        province = request.json.get('province')
        address1 = request.json.get('address1')
        address2 = request.json.get('address2')
        tel_country_code = request.json.get('tel_country_code')
        tel = request.json.get('tel')

    args:
        - request_json (json) : request.json in handlers
        - lang (str) : language to be output

    returns:
        - errors (list) : list of Error object defined in api_errors.py
    """

    # check submitted values
    errors = []
    # 1. check required fields are satisfied
    required_fields = [
        'zipcode', 'city', 'province', 'address1', 'lat', 'lng',
        'tel_country_code', 'tel',
    ]
    for key in required_fields:
        if not request_json.get(key):
            errors.append(RequiredFieldsNotSatisfied(
                key, request_json.get(key), lang))
    if len(errors):
        return errors
    # 2. validate each field
    for key, value in request_json.items():
        print(f'{key}: {value}')
        if key in [
                'zipcode', 'city', 'province', 'address1', 'address2',
                'tel_country_code', 'tel']:
            if value and (not isinstance(value, str)):
                errors.append(InvalidFormatError(key, value, lang))
        if key in ['zipcode']:
            if not re.match(Validator.zipcode_regex, value):
                errors.append(InvalidZipCodeFormatError(key, value, lang))
        if key in ['tel_country_code']:
            if value not in Country.__dials__.values():
                errors.append(InvalidTelCountryCodeFormatError(key, value, lang))
        if key in ['lat', 'lng']:
            if not (isinstance(value, float) or
                    (isinstance(value, str) and
                        value.replace('.', '', 1).isdigit())):
                errors.append(InvalidLatLngFormatError(key, value, lang))
        if key in ['tel']:
            if not re.match(Validator.tel_regex, value):
                errors.append(InvalidTelFormatError(key, value, lang))

    if len(errors):
        logging.info(f'{len(errors)} errors found in values.')
        return errors
    else:
        return []


def validate_organization_member_basics(request_json, lang) -> list:
    """Validate OrganizationMember paramters (Page 3 in signup).

    args:
        - request_json (json) : request.json in handlers
        - lang (str) : language to be output

        # Page 3
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
        if key in ['first_name', 'last_name']:
            if OrganizationMember.__max_name_length__ < len(value):
                errors.append(
                    NameTooLongError(
                        key, value,
                        OrganizationMember.__max_name_length__, lang))
        if key in ['email']:
            if not re.match(Validator.email_regex, value):
                errors.append(InvalidEmailFormatError(key, value, lang))
        if key in ['password']:
            if not re.match(
                    Validator.password_at_least_one_alphabet_regex, value):
                errors.append(
                    PasswordContainsNoAlphabetError(key, value, lang))
            if not re.match(
                    Validator.password_at_least_one_numeric_regex, value):
                errors.append(PasswordContainsNoNumberError(key, value, lang))
            if not re.match(
                    Validator.password_complete_regex, value):
                errors.append(InvalidPasswordFormatError(key, value, lang))
        if key in ['password_confirm']:
            if request_json.get('password') != value:
                errors.append(
                    ConfirmationPasswordNotCorrespondingError(key, value, lang))

    if len(errors):
        logging.info(f'{len(errors)} errors found in values.')
        return errors


# API Handlers

@blueprint_organizations.route('/organizations/signup', methods=['POST'])
def organizations_signup():
    """Signup an account.

    /organizations/signup [POST]

    params:
        # page 1
        - organization_name (str) :
        - organization_type (int) : OrganizationType
        - country (str) : Country.name
        # page 2
        - city (str) : 
        - province (str) : 
        - address1 (str) :
        - address2 (str) :
        - tel_country_code (str) :
        - tel (str) :
        # page 3
        - first_name (str) :
        - last_name (str) :
        - email (str) :
        - password (str) :
        - password_confirm (str) :
    """
    logging.info('/organizations/signup [POST]')
    logging.info(request.json)

    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    page = request.args.get('page')
    lang = Locale.getlang(request)
    # Page 1
    organization_name = request.json.get('organization_name')
    organization_type = request.json.get('organization_type')
    business_description = request.json.get('business_description')
    country = request.json.get('country')
    # Page 2
    zipcode = request.json.get('zipcode')
    city = request.json.get('city')
    province = request.json.get('province')
    address1 = request.json.get('address1')
    address2 = request.json.get('address2')
    lat = request.json.get('lat')
    lng = request.json.get('lng')
    tel_country_code = request.json.get('tel_country_code')
    tel = request.json.get('tel')
    # Page 3
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    email = request.json.get('email')
    password = request.json.get('password')
    password_confirm = request.json.get('password_confirm')
 
    logging.info(f'new organization signed up \nname: {organization_name}\
        \nmember: {first_name} {last_name}')
    logging.info(f'page=> {page}')

    # validate submitted values
    errors = []
    # page 1
    errors_1 = validate_organization_basics(request.json, lang)
    logging.debug(errors_1)
    if page and int(page) == 1:
        if errors_1:
            raise ValidationError(errors_1)
        else:
            return OK('all parameters are valid.').json()
    # page 2
    errors_2 = validate_organization_contact(request.json, lang)
    if page and int(page) == 2:
        if errors_2:
            raise ValidationError(errors_2, lang)
        else:
            return OK('all parameters are valid.').json()
    # page 3
    errors_3 = validate_organization_member_basics(request.json, lang)
    if page and int(page) == 3:
        if errors_3:
            raise ValidationError(errors_3, lang)
        else:
            return OK('all parameters are valid.').json()
    # all pages
    errors += errors_1 if errors_1 else []
    errors += errors_2 if errors_2 else []
    errors += errors_3 if errors_3 else []
    if len(errors):
        raise ValidationError(errors, lang)

    # encrypt password
    cipher = Cipher()
    member_password_encrypted = cipher.encrypt(password)

    # save Organization account
    organization = Organization({
        '_id': ObjectId(),
        'name': organization_name,
        'type': organization_type,
        'business_description': business_description,
        'country': country,
        'zipcode': zipcode,
        'city': city,
        'province': province,
        'address1': address1,
        'address2': address2,
        'lat': float(lat),
        'lng': float(lng),
        'tel_country_code': tel_country_code,
        'tel': tel,
    })

    # save Organization Member account
    session_id = OrganizationMember.incrementalId(
        'session_id')
    organization_member = OrganizationMember({
        '_id': ObjectId(),
        'organization_id': organization._id,
        'first_name': first_name,
        'last_name': last_name,
        'session_id': session_id,
        'email': email,
        'password': member_password_encrypted,
        'role': OrganizationMemberRole.ADMIN.value,
        'mail_validation_code': secrets.token_urlsafe(32),
        'mail_validation_code_expired_datetime': expiration_datetime(
            after_hours=Config.SIGNUP_VERIFICATION_CODE_EXPIRATION_HOUR)
    })

    # check if user already exists
    exists = OrganizationMember.findOne({'email': organization_member.email})
    if exists:
        raise UserAlreadyExistsError('email', organization_member.email)

    # save organization
    try:
        organization.save()
    except Exception as e:
        raise SaveError('organization', str(e))

    # save organization member
    try:
        organization_member.save()
    except Exception as e:
        raise SaveError('organization_member', str(e))

    logging.debug(
        f'organization: \n_id:{organization._id}\n\
        name:{organization.name}\nsaved.')
    logging.debug(
        f'organization member: \n_id:{organization_member._id}\n\
        name:{organization_member.first_name} {organization_member.last_name}\
        \nsaved.')

    # start session
    OrganizationMemberSession.start(session_id)

    # send a verification to the new_email
    try:
        Mail.send_mail(
            subject=mail_titles['signup_organization'].en,  # TODO: switch language by user's locale
            text=render_signup_organization(
                organization_member,
                validation_url=f'{Config.HOST_URL}/organizations/signup/confirm?email={email}&mail_validation_code={organization_member.mail_validation_code}',
                lang=lang,
                html=False),
            html=render_signup_organization(
                organization_member,
                validation_url=f'{Config.HOST_URL}/organizations/signup/confirm?email={email}&mail_validation_code={organization_member.mail_validation_code}',
                lang=lang,
                html=True),
            recipient_email=email
        )
    except Exception as e:
        raise EmailSentFailed('email', email, e, lang)
    else:
        return jsonify({
            'saved_data': {
                'organization': organization.response_json(),
                'organization_member': organization_member.response_json(),
            },
            'success': {
                'code': SuccessCode.CREATED.value,
                'message': 'new organization created.'
            },
        }), SuccessCode.CREATED.value


@blueprint_organizations.route(
    '/organizations/signup/confirm', methods=['GET'])
def organizations_signup_confirm():
    """Check confirmation code.

    /organizations/signup/confirm [GET]

    args:
        - mail_validation_code (int) : 
    """
    logging.info('/organizations/signup/confirm [GET]')
    logging.info(request.args)

    # locale
    lang = Locale.getlang(request)

    # get data
    mail_validation_code = request.args.get('mail_validation_code')
    email = request.args.get('email')

    # fetch user
    organization_member = OrganizationMember.findOne(
        {'email': email})
    if not organization_member:
        raise OrganizationMemberNotFoundError(email, lang)
    logging.debug(
        f'organization_member {organization_member._id} found by\
        email {email}.')

    # fetch organization
    organization = Organization.findOne(
        {'_id': organization_member.organization_id})
    if not organization:
        raise OrganizationNotFoundError(
            organization_member.organization_id, lang)

    # check validation_code
    if organization_member.mail_validation_code != mail_validation_code:
        raise MailValidationCodeNotCorrespondingError(
            'mail_validation_code',
            mail_validation_code, lang)

    # check expired
    # TODO:

    # update organization member
    try:
        organization_member.verified = True
        organization_member.update()
    except Exception as e:
        raise SaveError('organization_member', str(e), lang)

    # start session
    OrganizationMemberSession.start(organization_member.session_id),

    # return jsonify({
    #     'saved_data': organization_member.response_json(),
    #     'success': {
    #         'code': SuccessCode.CREATED.value,
    #         'message': 'organization_member verified.'
    #     },
    # }), SuccessCode.CREATED.value
    locale_dict = Locale(f'{Config.MESSAGES_ROOT}/signup_confirm.json').dict()
    return render_template(
        'business/pages/signup_confirm.html',
        organization=organization,
        organization_member=organization_member,
        locale_dict=locale_dict, lang=lang)


@blueprint_organizations.route('/organizations/signin', methods=['POST'])
def organizations_signin():
    """Signin to an account.

    /organizations/signin [POST]

    params:
        - email : str
        - password : str
    """
    logging.info('/organizations/signin [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # check submitted values
    errors = []
    # 1. check required fields are satisfied
    required_fields = ['email', 'password']
    for key in required_fields:
        if not request.json.get(key):
            errors.append(
                RequiredFieldsNotSatisfied(key, request.json.get(key), lang))
    if len(errors):
        raise ValidationError(errors, lang)

    # get data
    email = request.args.get('email')
    password = request.args.get('password')

    # find user
    organization_member = OrganizationMember.findOne({'email': email})

    # if user not found
    if not organization_member:
        raise OrganizationMemberNotFoundError(organization_member, lang)
    logging.debug(
        f'organization member {organization_member.session_id}\
          from email {organization_member.email} found.')

    # check password
    cipher = Cipher()
    if not cipher.iscorresponded(password, organization_member.password):
        raise PasswordIncorrectError(email, lang)
    logging.debug('password corresponded.')

    # start session
    logging.debug('start session.')
    OrganizationMemberSession.start(organization_member.session_id)

    return jsonify({
        'saved_data': None,
        'session_id': organization_member.session_id,
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'Logged in successfully.'
        }
    }), SuccessCode.OK.value


@blueprint_organizations.route(
    '/organizations/organization/update', methods=['POST'])
def organizations_organization_update():
    """Update organizations properties.

    /organizations/organization/update [POST]

    params:
       - organization_name (str) : (optional)
       - organization_type (int) : (optional) OrganiztionType.value
       - organization_country (str) : (optional) Country.name
       - zipcode (str) : (optional)
       - city (str) : (optional)
       - province (str) : (optional)
       - address1 (str) : (optional)
       - address2 (str) : (optional)
       - tel1 (str) : (optional)
       - tel2 (str) : (optional)
       - tel3 (str) : (optional)
    """
    logging.info('/organizations/organization/update [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # user_id from login session
    session_id = OrganizationMemberSession.user_id()
    if not session_id:
        raise SessionDoesntExistError(lang)

    # fetch user
    organization_member = OrganizationMember.findOne(
        {'session_id': session_id})
    if not organization_member:
        raise OrganizationMemberNotFoundError(session_id, lang)
    logging.debug(
        f'organization_member {organization_member._id}\
          found by user_id {session_id}.')

    # fetch organization
    organization = Organization.findOne(
        {'_id': organization_member.organization_id})
    if not organization:
        raise OrganizationNotFoundError(
            organization_member.organization_id, lang)

    # check privileges
    if not OrganizationMemberRole.is_authorized_admin_action(
            organization_member.role):
        raise OrganizationMemberPermissionDeniedError(
            organization_member.user_id)

    # check parameters
    errors = []
    errors_1 = validate_organization_basics(request.json)
    if errors_1:
        errors += errors_1
    errors_2 = validate_organization_contact(request.json)
    if errors_2:
        errors += errors_2
    if len(errors):
        logging.debug(errors)
        raise ValidationError(errors, lang)
 
    # update organization
    try:
        organization.update()
    except Exception as e:
        raise SaveError('organization update', str(e))
    logging.debug(f'organization {organization._id} \
        updated for keys {request.json.keys()}')

    return jsonify({
        'saved_data': organization.response_json(),
        'organization_id': str(organization._id),
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'organization data successfully updated.'
        }
    }), SuccessCode.OK.value


@blueprint_organizations.route(
    '/organizations/member/update', methods=['POST'])
def organizations_member_update():
    """Update organization member's properties.

    /organizations/member/update [POST]

    params:
       - first_name (str) : (optional)
       - last_name (str) : (optional)
       - country (str) : (optional) Country.name
       - zipcode (str) : (optional)
       - city (str) : (optional)
       - province (str) : (optional)
       - address1 (str) : (optional)
       - address2 (str) : (optional)
       - tel1 (str) : (optional)
       - tel2 (str) : (optional)
       - tel3 (str) : (optional)
    """
    logging.info('/organizations/member/update [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # organization member id from login session
    session_id = OrganizationMemberSession.user_id()
    if not session_id:
        raise SessionDoesntExistError(lang)

    # fetch user
    organization_member = OrganizationMember.findOne(
        {'session_id': session_id})
    if not organization_member:
        raise OrganizationMemberNotFoundError(session_id, lang)
    logging.debug(f'organization_member {organization_member._id}\
        found by user_id {session_id}.')

    # check parameters
    errors = validate_organization_member_basics(request.json)
    if errors:
        logging.debug(errors)
        raise ValidationError(errors, lang)
 
    # update organization
    organization_member.update()
    logging.debug(f'organization {organization_member._id} \
        updated for keys {request.json.keys()}')

    return jsonify({
        'saved_data': organization_member.response_json(),
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'organization member successfully updated.'
        }
    }), SuccessCode.OK.value


@blueprint_organizations.route(
    '/organizations/member/role/update', methods=['POST'])
def organizations_member_role_update():
    """Update organization member's role.

    /organizations/member/role/update [POST]

    params:
        - target_member_id (str) : OrganizationMember._id
        - role (int) : (optional) OrganizationMemberRole.value
    """
    logging.info('/organizations/member/role/update [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # fetch data
    target_member_id = request.json.get('target_member_id')
    role = request.json.get('role')

    # user_id from login session
    session_id = OrganizationMemberSession.user_id()
    if not session_id:
        raise SessionDoesntExistError(lang)

    # fetch user
    organization_member = OrganizationMember.findOne(
        {'session_id': session_id})
    if not organization_member:
        raise OrganizationMemberNotFoundError(session_id, lang)
    logging.debug(f'organization_member {organization_member._id} \
        found by user_id {session_id}.')

    # check privileges
    if not OrganizationMemberRole.is_authorized_admin_action(
            organization_member.role):
        raise OrganizationMemberPermissionDeniedError(
            organization_member.session_id, lang)
    
    # check if the only admin user is resigning
    if target_member_id == organization_member.session_id\
            and organization_member.is_only_admin():
        raise OrganizationMemberCannotResignAdminRoleError(
            target_member_id, lang)

    # update role
    try:
        organization_member.role = role
        organization_member.update()
    except Exception as e:
        raise SaveError(organization_member._id, str(e), lang)
    logging.debug(f'organization member {organization_member._id}\'s role updated to {OrganizationMemberRole(role).name}')

    return jsonify({
        'saved_data': organization_member.response_json(),
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'organization member\'s role successfully updated.'
        }
    }), SuccessCode.OK.value


@blueprint_organizations.route(
    '/organizations/member/email/update', methods=['POST'])
def organizations_member_email_update():
    """Update organization member's email.

    1. check if user's input of current email is correct
    2. send a verification to the new email address
    3. return a response

    /organizations/member/email/update [POST]

    params:
        - current_email (str) :
        - new_email (str) : 
    """
    logging.info('/organizations/member/email/update [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)
 
    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    current_email = request.json.get('current_email')
    new_email = request.json.get('new_email')

    # organization member id from login session
    session_id = OrganizationMemberSession.user_id()
    if not session_id:
        raise SessionDoesntExistError(lang)

    # fetch organization_member
    organization_member = OrganizationMember.findOne(
        {'session_id': session_id})
    if not organization_member:
        raise OrganizationMemberNotFoundError(session_id, lang)
    logging.debug(f'organization_member {organization_member._id} found by session_id {session_id}.')

    # check if current_email is corresponding
    if not organization_member.email == current_email:
        raise EmailNotCorrespondingError(current_email, lang)

    # check if new_email format is valid
    if not(new_email) or not re.match(Validator.email_regex, new_email):
        raise InvalidEmailFormatError(new_email, lang)

    # check if new email is already in use   
    if OrganizationMember.findOne(
            {'email': new_email}):
        raise UserAlreadyExistsError('email', new_email, lang)

    # generate validation code
    organization_member.mail_validation_code = secrets.token_urlsafe(32)
    organization_member.new_email = new_email

    # update organization member
    try:
        organization_member.update()
    except Exception as e:
        raise SaveError(organization_member._id, str(e))
    logging.debug(f'organization member {organization_member._id} updated.')

    # send a verification to the new_email
    try:
        Mail.send_mail(
            subject=mail_titles['email_change_verification'].en,  # TODO: switch language by organization_member's locale
            text=render_email_change_verification_organization_member(
                organization_member,
                validation_url=f'{Config.HOST_URL}\
                    ?code={organization_member.mail_validation_code}',
                lang='en', html=False),
            html=render_email_change_verification_organization_member(
                organization_member,
                validation_url=f'{Config.HOST_URL}\
                    ?code={organization_member.mail_validation_code}',
                lang='en', html=True),
            recipient_email=new_email
        )
    except Exception as e:
        raise EmailSentFailed(new_email, e, lang)
    else:
        return jsonify({
            'saved_data': organization_member.response_json(),
            'session_id':
                organization_member.session_id,
            'new_email': new_email,
            'success': {
                'code': SuccessCode.OK.value,
                'message': 'updating email validation code sent.'
            }
        }), SuccessCode.OK.value


@blueprint_organizations.route(
    '/organizations/member/email/update/verify', methods=['GET'])
def organizations_email_verify():
    """Verify organization member's email.

    /organizations/email/update/verify [POST]

    params:
        - mail_validation_code (int) :
    """
    logging.info('/organizations/member/email/update/verify [GET]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    mail_validation_code = request.args.get('mail_validation_code')

    # validate parameters
    if not mail_validation_code or not \
            re.match(Validator.numeric_only_regex, mail_validation_code):
        raise InvalidFormatError('mail_validation_code', mail_validation_code)

    # session id from context
    session_id = OrganizationMemberSession.user_id()
    if not session_id:
        raise SessionDoesntExistError(lang)

    # fetch user
    organization_member = OrganizationMember.findOne(
        {'session_id': session_id})
    if not organization_member:
        raise UserNotFoundError(organization_member, lang)
    logging.debug(f'organization_member {organization_member._id} \
        found by user_id {session_id}.')

    # check confirmation_code
    if organization_member.mail_validation_code != mail_validation_code:
        raise MailValidationCodeNotCorrespondingError(mail_validation_code, lang)
    
    # update organization member
    try:
        previous_email = organization_member.email
        new_email = organization_member.new_email
        organization_member.email = new_email
        organization_member.new_email = ''
        organization_member.update()
    except Exception as e:
        raise SaveError('email', new_email, str(e))

    return jsonify({
        'saved_data': organization_member.response_json(),
        'previous_email': previous_email,
        'new_email': new_email,
        'success': {
            'code': SuccessCode.OK.value,
            'message': f'organization_member\'s email updated from \
                {previous_email} to {new_email}.'
        },
    }), SuccessCode.OK.value


@blueprint_organizations.route(
    '/organizations/member/password/update', methods=['POST'])
def organizations_password_update():
    """Update organization member's password while signing in.

    /organizations/member/password/update [POST]

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
    logging.info('/organizations/member/password/update [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    previous_password = request.json.get('previous_password')
    new_password = request.json.get('new_password')
    new_password_confirm = request.json.get('new_password_confirm')

    # organization member id from context
    session_id = OrganizationMemberSession.user_id()
    if not session_id:
        raise SessionDoesntExistError(lang)

    # fetch organization member
    organization_member = OrganizationMember.findOne(
        {'session_id': session_id})
    if not organization_member:
        raise OrganizationMemberNotFoundError(session_id, lang)
    logging.debug(f'found organization_member {organization_member.email} \
        in session.')

    # check previous password
    cipher = Cipher()
    if not cipher.iscorresponded(
            previous_password, organization_member.password):
        raise PreviousPasswordIncorrectError(organization_member.email, lang)
    
    # check if new passwords are correctly input
    if new_password != new_password_confirm:
        raise NewPasswordsNotCorrespondingError(organization_member.email, lang)

    # send password reset success mail
    try:
        Mail.send_mail(
            subject=mail_titles['password_change_success'].en,  # TODO: switch language by organization_member's locale
            text=render_password_change_success_organization_member(
                organization_member, lang='en', html=False),
            html=render_password_change_success_organization_member(
                organization_member, lang='en', html=True),
            recipient_email=organization_member.email
        )
    except Exception as e:
        raise EmailSentFailed(organization_member.email, e, lang)
    else:
        return jsonify({
            'saved_data': None,
            'email': organization_member.email,
            'success': {
                'code': SuccessCode.OK.value,
                'message': 'password was changed successfully.'
            }
        }), SuccessCode.OK.value


@blueprint_organizations.route(
    '/organizations/member/password/request/reset', methods=['POST'])
def organizations_login_():
    """Send password reset mail.

    /organizations/member/password/request/reset [POST]

    *NOTICE
    No session is assumed.

    Because this API is used when a user lost password.
    Or some problems occur when a user tried to signin.

    When this request is submit,

        1. 5 digits number of password_reset_code
        2. password reset link

    is sent to the email address.

    args:
        - email (str): the email where the reset code and the link to be sent.
    """
    logging.info('/organizations/member/password/reset [POST]')

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    email = request.json.get('email')

    # fetch user
    organization_member = OrganizationMember.findOne(
        {'email': email})
    if not organization_member:
        raise OrganizationMemberNotFoundError('email', email)
    logging.debug(f'found organization_member {organization_member.email} \
        in session.')

    # generate password reset code and expiration date
    try:
        password_reset_code = secrets.randbits(16)
        organization_member.password_reset_code = password_reset_code
        organization_member.password_reset_code_expiration = \
            expiration_datetime(after_hours=48)
        organization_member.update()
    except Exception as e:
        raise SaveError(
            'password_reset_code', password_reset_code, str(e), lang)

    # send login recovery mail
    try:
        Mail.send_mail(
            subject=mail_titles['password_reset'].en,  # TODO: switch language by organization_member's locale
            text=render_password_reset_organization_member(
                organization_member,
                lang='en',
                password_reset_code=organization_member.password_reset_code,
                html=False),
            html=render_password_reset_organization_member(
                organization_member,
                lang='en',
                password_reset_code=organization_member.password_reset_code,
                html=True),
            recipient_email=organization_member.email
        )
    except Exception as e:
        raise EmailSentFailed(organization_member.email, e, lang)
    else:
        return jsonify({
            'saved_data': organization_member.response_json(),
            'session_id':
                organization_member.session_id,
            'email': organization_member.email,
            'success': {
                'code': SuccessCode.OK.value,
                'message': f'login recovery mail was successfully sent to \
                    {organization_member.email}.'
            }
        }), SuccessCode.OK.value


@blueprint_organizations.route(
    '/organizations/member/password/reset', methods=['POST'])
def organizations_password_reset():
    """Reset organization member's password.

    /organizations/member/password/reset [POST]

    The user who lost password reset to a new password by
    using the "password_reset_code" sent to the email address
    from the request of /organizations/member/password/request/reset 

    params:
        - email (str) :
        - password_reset_code (str) : guarantee the one who requested is the owner of the email.
        - new_password (str) :
        - new_password_confirm (str) :
    """
    logging.info('/organizations/member/password/reset [POST]')
    logging.info(request.json)

    # locale
    lang = Locale.getlang(request)

    # check request header
    if request.headers['Content-Type'] not in (
            'application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    email = request.json.get('email')
    new_password = request.json.get('new_password')
    new_password_confirm = request.json.get('new_password_confirm')
    password_reset_code = request.json.get('password_reset_code')

    # fetch user
    organization_member = OrganizationMember.findOne({'email': email})
    if not organization_member:
        raise OrganizationMemberNotFoundError(email, lang)
    logging.debug(f'found organization_member {organization_member.email} in session.')

    # check reset code validity
    if organization_member.password_reset_code != password_reset_code:
        raise InvalidPasswordResetCodeError(password_reset_code, lang)

    # check correspondance
    if new_password != new_password_confirm:
        raise NewPasswordsNotCorrespondingError(new_password, lang)

    # check format
    if not re.match(Validator.password_complete_regex, new_password):
        raise InvalidPasswordFormatError(new_password, lang)

    # update password
    cipher = Cipher()
    organization_member.password = cipher.encrypt(new_password)

    # send password change success mail
    try:
        Mail.send_mail(
            subject=mail_titles['password_change_success'].en,  # TODO: switch language by organization_member's locale
            text=render_password_change_success_organization_member(
                organization_member, lang='en', html=False),
            html=render_password_change_success_organization_member(
                organization_member, lang='en', html=True),
            recipient_email=organization_member.email
        )
    except Exception as e:
        raise EmailSentFailed(organization_member.email, e, lang)
    else:
        return jsonify({
            'saved_data': None,
            'session_id':
                organization_member.session_id,
            'email': organization_member.email,
            'success': {
                'code': SuccessCode.OK.value,
                'message': f'password successfully changed for organization_member {organization_member.session_id}.'
            }
        }), SuccessCode.OK.value


@blueprint_organizations.route('/organizations/icon/upload', methods=['POST'])
def organizations_icon_update():
    """Upload organizations icon.

    /organizations/icon/upload [POST]

    params:
    """
    logging.info('/organizations/icon/upload [POST]')
    logging.info(request.json)

    # check request header
    if request.headers['Content-Type'] not in \
            ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data

    pass


@blueprint_organizations.route('/organizations/exists', methods=['POST'])
def organizations_check_exists():
    """Check if the organization member already exists.

    /organizations/exists [POST]

    params:
        - email : str
    """

    # locale
    lang = Locale.getlang(request)

    email = request.json.get('email')

    if not email:
        raise InvalidEmailFormatError(email, lang)

    exists = OrganizationMember.findOne({'email': email})
    if exists:
        return jsonify({
            'exists': True,
            'message': f'user from {email} already exists.'
        }), ErrorCode.CONFLICT.value
    else:
        return jsonify({
            'exists': False,
            'message': f'user from {email} doesn\'t exist.'
        }), SuccessCode.OK.value
