#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/contents.py
#
# contents API list:
#
#  /v1/contents/guide/texts/create [POST]
#
#      - name (int) : 
#      - title (int) : 
#      - text (str) :
#      - language (str) : Language.name eg. JA
#
#  /v1/contents/guide/text/update [POST]
#
#      - index (int) : unique in the organization
#      - name (int) : 
#      - title (int) : 
#      - text (str) :
#      - language (str) : Language.name eg. JA
#      - done (bool) : True if the edit looks done.
#
#  /v1/contents/guide/text/delete [POST]
#
#      - index (int) : text content index
#      - language (str) : eg. ja
#
#  /v1/contents/guide/text/list [GET]
#
#

import sys
import logging
from bson import ObjectId
from flask import jsonify, Blueprint, request
from flask_httpauth import HTTPBasicAuth
sys.path.append('../')
from helpers.validator import Validator
from api.api_response import SuccessResponse, ErrorResponse, SuccessCode, ErrorCode
from api.responses.api_errors import SessionDoesntExistError, InvalidContentType, \
    SaveError, OrganizationMemberNotFoundError, ContentNotFoundError, \
    InvalidNameLength, InvalidTitleLength, InvalidTextLength, \
    InvalidLanguage, InvalidIndex
from helpers.mail import Mail
from helpers.s3 import put_text
from helpers.dateutils import expiration_datetime
from models.content import Content
from models.enums.media_type import MediaType
from models.enums.language import Language
from tools.sessions import OrganizationMemberSession


auth = HTTPBasicAuth()
basic_auth_contents = {
    "citywalk": "klawytic"
}


@auth.get_password
def get_password(username):
    if username in basic_auth_contents:
        return basic_auth_contents.get(username)
    return None


blueprint_contents = Blueprint('contents', __name__)


# ERROR Handlers

@blueprint_contents.errorhandler(SessionDoesntExistError)
@blueprint_contents.errorhandler(InvalidContentType)
@blueprint_contents.errorhandler(SaveError)
@blueprint_contents.errorhandler(OrganizationMemberNotFoundError)
@blueprint_contents.errorhandler(ContentNotFoundError)
@blueprint_contents.errorhandler(InvalidNameLength)
@blueprint_contents.errorhandler(InvalidTitleLength)
@blueprint_contents.errorhandler(InvalidTextLength)
@blueprint_contents.errorhandler(InvalidLanguage)
@blueprint_contents.errorhandler(InvalidIndex)
def error_response(error):
    error_reponse = error.__error_obj__()
    return error_reponse


# API Handlers

@blueprint_contents.route('/v1/contents/guide/create', methods=['POST'])
def contents_guide_create():
    """Create new guide content.

    /v1/contents/guide/create [POST]

    params:
        - name (int) : 
        - title (int) : 
        - text (str) :
        - language (str) : Language.name eg. JA
    """
    logging.info('/v1/contents/guide/create [POST]')
    logging.info(request.json)

    # check request header
    if request.headers['Content-Type'] not in ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    name = request.json.get('name', type=str)
    title = request.json.get('title', type=str)
    text = request.json.get('text', type=str)
    language = request.json.get('language', type=str)

    logging.info(f'new guide content text posted \nindex: {index}\ntext: {text}\nlang: {language}')

    # check parameters
    if not Content.validate_name_length(name):
        raise InvalidNameLength(
            name, Content.__min_name_length, Content.__max_name_length__)
    if not Content.validate_title_length(title):
        raise InvalidTitleLength(
            title, Content.__min_title_length, Content.__max_title_length__)
    if not Content.validate_text_length(text):
        raise InvalidTextLength(
            text, Content.__min_text_length__, Content.__max_text_length__)

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

    # save Organization/OrganiationMember account
    content_id = ObjectId()
    index = Content.incrementalId()
    content = Content({
        '_id': content_id,
        'index': index,
        'type': MediaType.AUDIO_GUIDE,
        'name': name,
        'title': title,
        'text': text,
        'organization_id': organization_member.organization_id,
        'created_member_id': organization_member._id,
        'latest_edit_member_id': organization_member._id,
    })

    # save organization
    try:
        content.save()
    except Exception as e:
        raise SaveError('content', str(e))

    # save text content to versioning strage
    s3_url = put_text(text)

    logging.debug(f'content: \n_id:{content._id}\nindex:{content.index}\nname:{content.name}\ncreated.')

    return jsonify({
        'saved_data': content.response_json(),
        'returned_url': s3_url,
        'success': {
            'code': SuccessCode.CREATED.value,
            'message': 'new guide content created.'
        },
    }), SuccessCode.CREATED.value


@blueprint_contents.route('/v1/contents/guide/update', methods=['POST'])
def contents_guide_update():
    """Update guide content.

    /v1/contents/guide/update [POST]

    params:
        - index (int) : unique in the organization
        - name (int) : 
        - title (int) : 
        - text (str) :
        - language (str) : Language.name eg. JA
        - done (bool) : True if the edit looks done.
    """
    logging.info('/v1/contents/guide/create [POST]')
    logging.info(request.json)

    # check request header
    if request.headers['Content-Type'] not in ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    index = request.json.get('index', type=int)
    name = request.json.get('name', type=str)
    title = request.json.get('title', type=str)
    text = request.json.get('text', type=str)
    language = request.json.get('language', type=str)
    done = request.json.get('done', type=bool)

    logging.info(f'new guide content text posted \nindex: {index}\ntext: {text}\nlang: {language}')

    # validate parameters
    if not isinstance(index, int):
        raise InvalidContentIndexError(index)
    if not Language.is_valid_name(language):
        raise InvalidLanguageError(value)

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

    # fetch content
    content = Content.findOne({'organization_id': organization_member.organization_id, 'index': index, 'language': language})
    if not content:
        raise ContentNotFoundError(index, language)

    # check updating parameters
    for key, value in request.json.items():
        if key in ('name'):
            if not Content.validate_name_length(name):
                raise InvalidNameLength(name)
            else:
                content.name = value
        if key in ('title'):
            if not Content.validate_title_length(title):
                raise InvalidTitleLength(title)
            else:
                content.title = value
        if key in ('text'):
            if not Content.validate_text_length(text):
                raise InvalidTextLength(text)
            else:
                content.text = value

    # update content
    try:
        content.update()
    except Exception as e:
        raise SaveError('content', str(e))

    # save text content to versioning strage
    if done:
        s3_url = put_text(text)

    logging.debug(f'content {content._id} updated for keys {request.json.keys()}')

    return jsonify({
        'saved_data': content.response_json(),
        'returned_url': s3_url if s3_url else None,
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'content successfully updated.'
        }
    }), SuccessCode.OK.value


@blueprint_contents.route('/v1/contents/guide/delete', methods=['POST'])
def contents_guide_delete():
    """Delete a guide content.

    /v1/contents/guide/delete [POST]

    params:
        - index (int) : text content index
        - language (str) : eg. ja
    """
    logging.info('/v1/contents/guide/delete [POST]')
    logging.info(request.json)

    # check request header
    if request.headers['Content-Type'] not in ('application/json', 'application/json; charset=utf-8'):
        raise InvalidContentType(request.headers['Content-Type'])

    # get data
    index = request.json.get('index', type=int)
    language = request.json.get('language', type=str)

    logging.info(f'guide content index: {index} is trying to be deleted.')

    # validate parameters
    if not isinstance(index, int):
        raise InvalidIndex(index)
    if not Language.is_valid_name(language):
        raise InvalidLanguage(value)

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

    # fetch content
    content = Content.findOne({'organization_id': organization_member.organization_id, 'index': index, 'language': language})
    if not content:
        raise ContentNotFoundError(index, language)

     # update content
    try:
        content.delete = True
        content.update()
    except Exception as e:
        raise SaveError('content', str(e))

    logging.debug(f'content {content._id} logically deleted.')

    return jsonify({
        'saved_data': content.response_json(),
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'content successfully deleted.'
        }
    }), SuccessCode.OK.value

@blueprint_contents.route('/v1/contents/guide/list', methods=['GET'])
def contents_guide_list():
    """Fetch guide contents.

    /v1/contents/guide/list [GET]

    args:

    returns:
        contents (list) : list of Content objects

    """
    logging.info('/v1/contents/guide/list [GET]')

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

    # fetch content
    contents = Content.fetch(organization_member.organization_id, json=True)
    logging.debug(f'{len(contents)} content found.')

    return jsonify({
        'saved_data': None,
        'contents': contents,
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'contents successfully fetched.'
        }
    }), SuccessCode.OK.value

@blueprint_contents.route('/demo/1/contents/guide/list', methods=['GET'])
def contents_guide_list_demo_1():
    logging.info('/demo/1/contents/guide/list [GET]')

    # '_id': ObjectId,
    # 'index': int,  # eg. 12
    # 'media_type': str,  # eg. MediaType.AUDIO_GUIDE.name

    # 'label': str,  # eg. Giza Pyramid
    # 'title': str,  # eg. The secret of Giza Pyramid
    # 'text': str,  # eg. The Great Pyramid of Giza is the oldest pyramids in the Giza pyramid complex

    # 'resource_key': str,  # eg. {organization_id}_{index}_{lang}.wav
    # 'image_key': str,  # eg. {organization_id}_{index}.jpg

    # 'language': str,  # eg. Language.ja.name

    # 'organization_id': str,  # The organization who registered this content. ex) Organization._id

    # 'condition': dict,  # condition that this content is reached. for instance, age restriction
    # 'featured': bool,  # featured flag
    # 'importance': int,  # publishing priority

    # 'created_member_id': ObjectId,  # _id of the member who created this content  
    # 'latest_edit_member_id': ObjectId,  # _id of the member who last edited this content  

    # 'deleted': bool,  # True when user chose deleting. after deleted, hidden but enable to recover.

    member_id = ObjectId()

    # TODO: set member.name as author
    # TODO: set updated as the formatted string 'YYYY MM/dd hh:mm'

    contents = []
    contents.append(Content({
        '_id': ObjectId(),
        'index': 1,
        'media_type': MediaType.audio.name,
        'lat': 46.953976,
        'lon': 7.456123,
        'label': 'Giza Pyramid',
        'title': 'The secret of Giza Pyramid',
        'text': 'The Great Pyramid of Giza is the oldest pyramids in the Giza pyramid complex',
        'language': Language.en.name,
        'orgainzation_id': 1,
        'target': 0,
        'radius': 5,
        'created_member_id': member_id,
        'latest_edit_member_id': member_id,
    }))
    contents.append(Content({
        '_id': ObjectId(),
        'index': 2,
        'media_type': MediaType.audio.name,
        'lat': 46.933176,
        'lon': 7.440143,
        'label': 'Mona Lisa',
        'title': 'Mona Lisa Title and subject',
        'text': """\
 The title of the painting, which is known in English as Mona Lisa,
 comes from a description by Renaissance art historian Giorgio Vasari,
 who wrote "Leonardo undertook to paint,
 for Francesco del Giocondo, the portrait of Mona Lisa, his wife.
 """,
        'language': Language.en.name,
        'orgainzation_id': 1,
        'created_member_id': member_id,
        'latest_edit_member_id': member_id,
    }))
    contents.append(Content({
        '_id': ObjectId(),
        'index': 3,
        'media_type': MediaType.audio.name,
        'lat': 46.943956,
        'lon': 7.426124,
        'label': 'Renaissance',
        'title': 'Social and political structures in Italy',
        'text': """\
The unique political structures of late Middle Ages Italy \
have led some to theorize that its unusual social climate allowed \
the emergence of a rare cultural efflorescence.
""",
        'language': Language.en.name,
        'orgainzation_id': 1,
        'target': 0,
        'radius': 5,
        'created_member_id': member_id,
        'latest_edit_member_id': member_id,
    }))
    contents.append(Content({
        '_id': ObjectId(),
        'index': 4,
        'media_type': MediaType.audio.name,
        'lat': 46.943416,
        'lon': 7.439110,
        'label': 'ルネサンス',
        'title': '構成的な明暗法',
        'text': """\
暗い物体が、単一でしばしば目に見えない光源から放たれる一条の光によって劇的に照らされるという、
この構成的な明暗法を発展させた。
とくにカラヴァッジオは、劇的な明暗法が支配的な技法となるテネブリズムの発達に重大な貢献をした。
""",
        'language': Language.en.name,
        'orgainzation_id': 1,
        'created_member_id': member_id,
        'latest_edit_member_id': member_id,
    }))

    logging.debug(f'{len(contents)} content found.')

    contents = list(map(lambda x: x.response_json(), contents))
    logging.debug(contents)

    return jsonify({
        'saved_data': None,
        'contents': contents,
        'success': {
            'code': SuccessCode.OK.value,
            'message': 'contents successfully fetched.'
        }
    }), SuccessCode.OK.value