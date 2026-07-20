#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/country.py
#
# Country record from ISO3166
#
# based on:
# https://github.com/deactivated/python-iso3166/blob/master/iso3166/__init__.py
#
# country code data
# https://github.com/datasets/country-codes/blob/master/data/country-codes.csv
# header of country_codes.csv 
# FIFA,Dial,ISO3166-1-Alpha-3,MARC,is_independent,
# ISO3166-1-numeric,GAUL,FIPS,WMO,ISO3166-1-Alpha-2,
# ITU,IOC,DS,UNTERM,Spanish,
# Formal,Global,Code,Intermediate,Region,
# Code,official_name_fr,UNTERM,French,Short,
# ISO4217-currency_name,Developed,/,Developing,Countries,
# UNTERM,Russian,Formal,UNTERM,English,
# Short,ISO4217-currency_alphabetic_code,Small,Island,Developing,
# States,(SIDS),UNTERM,Spanish,Short,
# ISO4217-currency_numeric_code,UNTERM,Chinese,Formal,UNTERM,
# French,Formal,UNTERM,Russian,Short,
# M49,Sub-region,Code,Region,Code,
# official_name_ar,ISO4217-currency_minor_unit,UNTERM,Arabic,Formal,
# UNTERM,Chinese,Short,Land,Locked,
# Developing,Countries,(LLDC),Intermediate,Region,
# Name,official_name_es,UNTERM,English,Formal,
# official_name_zh,official_name_en,ISO4217-currency_country_name,Least,Developed,
# Countries,(LDC),Region,Name,UNTERM,
# Arabic,Short,Sub-region,Name,official_name_ru,
# Global,Name,Capital,Continent,TLD,
# Languages,Geoname,ID,CLDR,display,
# name,EDGAR
#
# generate:
# country_codes = {
#   'alpha2': [],
#   'numeric': [],
#   'dial': [],
#   'en': [],
#   'zh': [],
#   'fr': [],
#   'es': [],
#   'ja': [],
#   'ru': [],
#   'ar': [],
# }
# generate:
# class Country(EnumLocale):
#     JA = 398
#     US = 102
#     ...
#     name_en = {
#     }
#     name_ja = {
#        398: '日本',
#        102: 'アメリカ合衆国',
#        ...
#     }
#
# TODO: add column officail_japanese_name in CSV
# TODO: fix Taiwan (TW) codes and names in CSV

import sys
import csv
import json
import argparse
from collections import namedtuple
sys.path.append('../')
from libcommon.enumlocale import EnumLocale

CountryRecord = namedtuple(
    'CountryRecord',
    [
        'alpha2',  # ISO3166-1-Alpha-2 code
        'alpha3',  # ISO3166-1-Alpha-3 code
        'numeric',  # ISO3166-1-numeric code
        'dial',  # dial country code
        'name_en',  # English short name
        'name_zh',  # Chenese short name
        'name_fr',  # French short name
        'name_es',  # Espagne short name
        'name_ru',  # Russian short name
        'name_ar',  # Arabic short name
        #'name_ja'  # Japanese short name 
    ]
)

keys = [
    'ISO3166-1-Alpha-2',
    'ISO3166-1-Alpha-3',
    'ISO3166-1-numeric',
    'Dial',
    'official_name_en',
    'official_name_zh',
    'official_name_fr',
    'official_name_es',
    'official_name_ru',
    'official_name_ar',
    #'official_name_ja',
]

_records = []
with open('models/data/country_codes/country_codes.csv', newline='') as f:
    reader = csv.reader(f, delimiter=',')
    index = {}
    for i, row in enumerate(reader):
        # create dictionary of column indices
        if i == 0:
            for j, column_name in enumerate(row):
                # print(column_name)
                for key in keys:
                    if key == column_name:
                        index[column_name] = j
            # print(index)
        else:
            # print(index['ISO3166-1-Alpha-2'])
            # print(row[index['ISO3166-1-Alpha-2']])
            _records.append(
                CountryRecord(
                    row[index['ISO3166-1-Alpha-2']],
                    row[index['ISO3166-1-Alpha-3']],
                    row[index['ISO3166-1-numeric']],
                    row[index['Dial']],
                    row[index['official_name_en']],
                    row[index['official_name_zh']],
                    row[index['official_name_fr']],
                    row[index['official_name_es']],
                    row[index['official_name_ru']],
                    row[index['official_name_ar']],
                    #row[index['official_name_ja']],
                )
            )
    #print(_records)

# generate dictionary of country names and codes
country_codes = {
  'alpha2': [],
  'numeric': [],
  'dial': [],
  'en': [],
  'zh': [],
  'fr': [],
  'es': [],
  'ja': [],
  'ru': [],
  'ar': [],
}
for _record in _records:
    try:
        numeric = int(_record.numeric)
    except Exception as e:
        pass
        #print(f'{_record.name_en} failed.')
        #print(f'{e}')
    else:
        country_codes['alpha2'].append(_record.alpha2)
        country_codes['numeric'].append(_record.numeric)
        country_codes['dial'].append(_record.dial)
        country_codes['en'].append(_record.name_en)
        country_codes['zh'].append(_record.name_zh)
        country_codes['fr'].append(_record.name_fr)
        country_codes['es'].append(_record.name_es)
        #country_codes['ja'].append(_record.name_ja)
        country_codes['ru'].append(_record.name_ru)
        country_codes['ar'].append(_record.name_ar)


# generate Country model
# class Country(EnumLocale):
#     JA = 398
#     US = 102
#     ...
#     name_en = {
#     }
#     name_ja = {
#        398: '日本',
#        102: 'アメリカ合衆国',
#        ...
#     }
#
d = {}
__en__, __ja__, __zh__, __fr__, __es__, __ru__ = {}, {}, {}, {}, {}, {}
__dials__ = {}
for _record in _records:
    #print(_record.alpha2)
    #print(_record.alpha3)
    #print(_record.numeric)
    #print(_record.name_en)
    try:
        numeric = int(_record.numeric)
    except Exception as e:
        pass
        #print(f'{_record.name_en} failed.')
        #print(f'{e}')
    else:
        key = _record.alpha2 #country_record.name.upper().replace(' ', '_')  # e.g. JP
        index = int(_record.numeric)  # e.g. 392
        d[key] = index
        #__ja__[index] = _record.name_ja
        __en__[index] = _record.name_en
        __zh__[index] = _record.name_zh
        __fr__[index] = _record.name_fr
        __es__[index] = _record.name_es
        __ru__[index] = _record.name_ru
        __dials__[index] = _record.dial

Country = EnumLocale('Country', d)
Country.__dials__ = __dials__
Country.__en__ = __en__
#Country.__ja__ = __ja__
Country.__zh__ = __zh__
Country.__fr__ = __fr__
Country.__es__ = __es__
Country.__ru__ = __ru__

# TODO: move to makejson.py
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--generate_js', action='store_true', help='generate data/country_codes.json')
    args = parser.parse_args()

    if args.generate_js:
        with open('data/country_codes.json', 'w') as f:
            json.dump(country_codes, f)