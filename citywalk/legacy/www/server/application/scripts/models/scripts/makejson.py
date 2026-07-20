#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/scripts/makejson.py
#
# Make JSON files from enumerable definitions
#
# generate:
#   - js/data/organization_type.json
#   - js/data/item_type.json
#   - js/data/gender.json
#   - js/data/media_type.json
#   - js/data/target_segment.json
#   - js/data/language.json
#   - js/data/day.json
#   - js/data/action_type.json
#   - js/data/rating_type.json
#   - js/data/country_codes.json
#
# EnumLocale.to_dict() outputs
# {
#   "names": ["RED", "YELLOW", "BLUE"],
#   "values": [0, 1, 2],
#   "ja": ["赤", "黄", "青"],
#   "en": ["Red", "Yellow", "Blue"],
#   ...
# }
#

import json
import argparse
from models.enums.item_type import ItemType
from models.enums.gender import Gender
from models.enums.media_type import MediaType
from models.enums.target_segment import TargetSegment
from models.enums.organization_type import OrganizationType
from models.enums.organization_member_role import OrganizationMemberRole
from models.enums.language import Language
from models.enums.day import Day
from models.enums.action_type import ActionType
from models.enums.rating_type import RatingType
from models.enums.country import country_codes


def write_js(
        dic: dict, json_folder_name: str, json_file_name: str,
        js_file_name: str, class_name: str):
    """Write json & js file.

    eg. 
    # country_codes.json
    with open('models/data/country_codes/country_codes.json', 'w') as f:
        json.dump(country_codes, f)
    # countries.js
    with open('../views/src/ECMA/data/countries.js', 'w') as f:
        json_text = json.dumps(country_codes)
        f.seek(0)
        f.write('\"use strict\";\nconst countriesISO3166 = ' + json_text)

    args:
        - dic (dictionary) : dictionary object to be dumped as json text
        - json_folder_name (str) : models/data/{here}
        - json_file_name (str) : models/data/{json_folder_name}/{here}.json
        - js_file_name (str) : views/src/ECMA/data/{here}.js
        - class_name (str) : const {class_name} = {...}
    """
    # write json file to scripts/models/data
    with open(f'models/data/{json_folder_name}/{json_file_name}.json', 'w') as f:
        json.dump(dic, f)
    # write js file to views/src/ECMA/data
    with open(f'../views/src/ECMA/data/{js_file_name}.js', 'w') as f:
        json_text = json.dumps(dic)
        f.seek(0)
        f.write(f'\"use strict\";\nconst {class_name} = ' + json_text)
 

def write_js_multiply(
        dics: list, json_folder_name: str, json_file_names: list,
        js_file_name: str, class_names: list):
    """Write multiple json & compile into 1 single js file.

    args:
        - dics ([dictionary]) : list of dictionary object to be dumped as json text
        - json_folder_name (str) : models/data/{here}
        - json_file_names ([str]) : models/data/{json_folder_name}/{here}.json
        - js_file_name (str) : views/src/ECMA/data/{here}.js
        - class_names ([str]) : const {class_name} = {...}
    """
 

    # text which will be written as a js file
    text_to_write = "\"use strict\";\n"

    # wite all json and make all js text
    for i, d in enumerate(dics):
        # write json file to scripts/models/data
        with open(f'models/data/{json_folder_name}/{json_file_names[i]}.json', 'w') as f:
            json.dump(d, f)
            json_text = json.dumps(d)
            js_text = f'const {class_names[i]} = ' + json_text
            text_to_write += js_text
            text_to_write += "\n"

    # write js file to views/src/ECMA/data
    with open(f'../views/src/ECMA/data/{js_file_name}.js', 'w') as f:
        f.write(text_to_write)
 

def make_all():
    """Make all json files.
    """
    # country_codes/country_codes.json -> ECMA/data/countries.js
    write_js(
        country_codes, 'country_codes',
        'country_codes', 'countries', 'countriesISO3166')

    # wite all these json files
    # enums/organization_type.json
    # enums/item_type.json
    # enums/target_segment.json
    # enums/gender.json
    # enums/media_type.json
    # enums/organization_member_role.json
    # enums/language.json
    # enums/day.json
    # enums/action_type.json
    # enums/rating_type.json

    # and compile them into a single js file
    # -> ECMA/data/enums.js
    write_js_multiply(
        dics=[
            OrganizationType.to_dict(),
            ItemType.to_dict(),
            TargetSegment.to_dict(),
            Gender.to_dict(),
            MediaType.to_dict(),
            OrganizationMemberRole.to_dict(),
            Language.to_dict(),
            Day.to_dict(),
            ActionType.to_dict(),
            RatingType.to_dict()
        ],
        json_folder_name='enums',
        json_file_names=[
            'organization_type',
            'item_type',
            'target_segment',
            'gender',
            'media_type',
            'organization_member_role',
            'language',
            'day',
            'action_type',
            'rating_type',
        ],
        js_file_name='enums',
        class_names=[
            'OrganizationType',
            'ItemType',
            'TargetSegment',
            'Gender',
            'MediaType',
            'OrganizationMemberRole',
            'Language',
            'Day',
            'ActionType',
            'RatingType',
        ]
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--all', action='store_true',
        help='generate all json files.')
    parser.add_argument(
        '--country_codes', action='store_true',
        help='generate data/country_codes.json')
    parser.add_argument(
        '--organization_type', action='store_true',
        help='generate data/organization_type.json')
    # TODO: all options
 
    args = parser.parse_args()

    if args.all:
        make_all()
    else:
        print('[WARNING] only --all option works so far. sorry.')

    # TODO:
    # if args.all or args.country_codes:
    #     with open('data/country_codes.json', 'w') as f:
    #         json.dump(country_codes, f)
    # if args.all or args.organization_type:
    #     with open('data/country_codes.json', 'w') as f:
    #         json.dump(OrganizationType.to_dict(), f)