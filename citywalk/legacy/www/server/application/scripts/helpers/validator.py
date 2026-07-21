#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# helpers/validator.py
#
# Copyright (c) 2021~ ThinkX,Inc All rights reserved.

import re
import os
import calendar
from general.exceptions import InvalidFormat
from general.exceptions import TextTooLong
from general.exceptions import TextTooShort
from general.exceptions import InvalidEmailFormat
from general.exceptions import InvalidPasswordFormat
from general.exceptions import ValueOutOfRange
from general.exceptions import EmptyFile
from general.exceptions import FileTooLarge
from general.exceptions import InvalidType


class Validator(object):
    """Validator.
    """
    email_regex = r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$"
    yyyymmdd_regex = r'^(?!([02468][1235679]|[13579][01345789])00-02-29)(([0-9]{4}-(01|03|05|07|08|10|12)-(0[1-9]|[12][0-9]|3[01]))|([0-9]{4}-(04|06|09|11)-(0[1-9]|[12][0-9]|30))|([0-9]{4}-02-(0[1-9]|1[0-9]|2[0-8]))|([0-9]{2}([02468][048]|[13579][26])-02-29))$'
    yyyymm_regex = r'^[12]\d{3}-(0[1-9]|1[0-2])$'
    hhmm_regex = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    hhmm_30min_regex = r'^([0-1]?[0-9]|2[0-3]):[03][0]$'
    password_at_least_one_alphabet_regex = r'.*[A-Za-z].*'
    password_at_least_one_numeric_regex = r'.*[0-9].*'
    password_complete_regex = r'[A-Za-z0-9@#$%^&+=]{8,}'
    numeric_only_regex = r'^[0-9]'
    # zipcode format
    #   ○ 1001111
    #   ○ 100-1111
    #   ○ 10-01111
    #   ○ A10-01111
    #   × 001-(4365) -> () symbols are not allowed
    zipcode_regex = r'^(?:[A-Z0-9]+([-]?[A-Z0-9]+)*)?$'
    zipcode_nohyphen_regex = r'^(?:[A-Z0-9]+([A-Z0-9]+)*)?$'
    # tel format
    #   ○ 08043651460
    #   ○ 080-4365-1460
    #   ○ +(080)-(4365)-1460
    #   × +(080)-(4365)-1460-1111 -> too many hyphen temrs
    #   × 000001-(4365)-1460 -> the first term is over 4digits
    #   × 0123456789012345 -> more than 4+5+6 digits
    tel_regex = r'^[\+]?[(]?[0-9]{2,4}[)]?[-\s\.]?[()]?[0-9]{3,5}[)]?[-\s\.]?[0-9]{3,6}$'

    @classmethod
    def validate_length(cls, min_length: int, max_length: int, key_name = ''):
        """Validate text length.

        args:
            - key_name (str) : the name of the string to be checked.
            - min_length (int) : minimum length
            - max_length (int) : max_length

        return:
            - validate (function) : validator function
        """
        def validate(value):
            assert len(key_name) > 0
            if value and len(value) < min_length:
                raise TextTooShort(
                    '{} must be longer than {}, but the length is {}'
                    .format(key_name, min_length, len(value)))
            elif value and len(value) > max_length:
                raise TextTooLong(
                    '{} must be shorter than {}, but the length is {}'
                    .format(key_name, max_length, len(value)))
            else:
                return True
        return validate

    @classmethod
    def validate_email_format(cls):
        """Validate email format.

        return:
            - validate (function) : validator function
        """
        def validate(value):
            if not re.match(cls.email_regex, value):
                raise InvalidEmailFormat('{} is invalid email address format'
                                         .format(value))
            else:
                return True
        return validate

    @classmethod
    def validate_password_format(cls):
        """Validate password format.

        1. 8~20 chars
        2. alphabet or numeric chars

        args:
            - 
        returns:
            - validate (function) : validator function
        """
        def validate(value):
            if not re.match(
                cls.password_at_least_one_alphabet_regex, value):
                raise InvalidPasswordFormat(
                    'Password must include at least one alphabet charactor.')

            if not re.match(
                cls.password_at_least_one_numeric_regex, value):
                raise InvalidPasswordFormat(
                    'Password must include at least one numeric charactor.')

            if not re.match(
                cls.password_complete_regex, value):
                raise InvalidPasswordFormat(
                    'Password must be 8~20 charactors.')

            return True
        return validate

    @classmethod
    def validate_numeric_format(cls, key_name = ''):
        """Validate numeric only format.

        returns:
            - validate (function) : validator function
        """
        def validate(value):
            if not re.match(
                cls.numeric_only_regex, value):
                raise InvalidFormat(
                    f'{key_name} accept only numeric charactors.')
            else:
                return True
        return validate

    @classmethod
    def validate_timetable(cls):
        """Validate timetable format.

        returns:
            - validate (function) : validator function
        """
        def validate(value):
            if not 'year' in value.keys():
                raise InvalidFormat(
                    f'the key "year" is necessary for a timetable.'
                )
            year = value['year']
            c = calendar.Calendar()
            months = list(range(1, 12+1))
            for month in months:
                if not str(month) in value.keys():
                    raise InvalidFormat(
                        f'the key of month {month} is necessary for a timetable.'
                    )
                days = c.itermonthdays(year=year, month=month)
                for day in days:
                    if not str(day) in value[str(month)]:
                        raise InvalidFormat(
                            f'the key of day {day} in month {month} is necessary in the timetable.'
                        )
                    if not '00' in value[str(month)][str(day)]:
                        raise InvalidFormat(
                            f'the key "00" of day {month}/{day} is necessary in the timetable.'
                        )
                    if not '30' in value[str(month)][str(day)]:
                        raise InvalidFormat(
                            f'the key "30" of day {month}/{day} is necessary in the timetable.'
                        )
            return True
        return validate

    @classmethod
    def validate_zipcode_format(cls, allow_hyphen=True):
        """Validate zipcode format.

        return:
            - validate (function) : validator function
        """
        def validate(value):
            regex = cls.zipcode_regex if allow_hyphen \
                else cls.zipcode_nohyphen_regex
            if not re.match(regex, value):
                raise InvalidEmailFormat('{} is invalid zipcode format'
                                         .format(value))
            else:
                return True
        return validate

    @classmethod
    def validate_rating_range(key_name, min_value, max_value):
        """Validate score of rating.

        args:
            - key_name (str) : the name of the string to be checked.
            - min_length (int) : minimum length
            - max_length (int) : max_length

        return:
            - validate (function) : validator function
        """
        def validate(cls, value):
            if not (value >= min_value and value <= max_value):
                raise ValueOutOfRange('{} is must be {} ~ {}'
                                      .format(key_name, min_value, max_value))
            else:
                return True
        return validate

    @classmethod
    def validate_file(cls, max_size):
        """Validate uploaded file.

        args:
            - max_size (int) : thes file cannot exceed this size.

        return:
            - validate (function) : validator function
        """
        def validate(f):
            f.seek(0, os.SEEK_END)
            f_size = f.tell()
            f.seek(0)
            if not f or f_size == 0:
                raise EmptyFile('Empty file')
            elif f_size > max_size:
                raise FileTooLarge(
                    'File size too large. It must be less than {} bytes.'
                    .format(max_size))
            else:
                return True
        return validate

    @classmethod
    def validate_type(cls, valid_types):
        def validate(value):
            if value not in valid_types:
                raise InvalidType(
                    '{} is not valid type'.format(value))
            else:
                return True
        return validate