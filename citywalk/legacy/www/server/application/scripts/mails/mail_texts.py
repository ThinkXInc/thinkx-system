#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/mail_texts.py
#
# TODO: generate every language's email formats automatically by this script
#
# CSV to locale dictionary
#
# This generates 2 dictionaries with the key as identical keys of emails,
# and the value as namedtuple objects with keys of language code.
#
# - email_titles (dict)
# - email_texts (dict)
#
# csv sources:
#   - mails/csv/mail_titles.csv
#   - mails/csv/mail_texts.csv  TODO: now texts are written directly
#
# example:
#   > signup_titles = email_titles['signup']
#   > print(signup_titles.en)
#   Welcome to this service.
# 
#

import os 
import csv
from collections import namedtuple

# read from csv
dir_path = os.path.dirname(os.path.realpath(__file__))
csv_path = f'{dir_path}/csv/mail_titles.csv'
keys = []
jas = []
ens = []
zhs = []
with open(csv_path, 'r') as f:
    for i, line in enumerate(f.readlines()):
        if i == 0:
            # skip header
            continue
        cols = line.replace('\n', '').split(',')
        keys += [cols[0]]
        jas += [cols[1]]
        ens += [cols[2]]
        zhs += [cols[3]]

MailTitles = namedtuple(
    'MailTitiles',
    [
        'ja',  # japanese text
        'en',  # english text
        'zh',  # chinese text
    ]
)

MailTexts = namedtuple(
    'MailTexts',
    [
        'ja',  # japanese text
        'en',  # english text
        'zh',  # chinese text
    ]
)

mail_titles = {}
for key, ja, en, zh in zip(keys, jas, ens, zhs):
    mail_titles[key] = MailTexts(ja, en, zh)

mail_texts = {}
for key, ja, en, zh in zip(keys, jas, ens, zhs):
    mail_texts[key] = MailTexts(ja, en, zh)
