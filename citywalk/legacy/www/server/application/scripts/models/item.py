#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/item.py
#
# Item model
#

import datetime
import calendar
import pymongo
from bson import ObjectId
from datetime import timedelta
from libcommon.enumlocale import EnumLocale
from libcommon.mongobase import MongoBase
from helpers.validator import Validator
from general.exceptions import InvalidFormat
from models.enums.day import Day


class StoreInfo(MongoBase):
    __collection__ = 'storeinfo'
    __structure__ = {
        '_id': ObjectId,

        'name': str,  # The official seller name who sell this item.
        'contact': str,   # The contact to be displayed ex) 03-1234-5678 | info@seller.com

        'zipcode': str,
        'country': int,  # ex) Country.JP.value
        'city': str,  # ex) Minato-ku
        'province': str,  # ex) Tokyo
        'address1': str,  # ex) Roppongi 7-7-7
        'address2': str,  # ex) Tri-Seven Roppongi 8F

        'address_sid': ObjectId,  # Address.sid for searching locale address

        'created': datetime.datetime,
        'updated': datetime.datetime
    }
    __required_fields__ = ['_id', 'name', 'contact', 'address']
    __default_values__ = {
    }
    __validators__ = {
        'name': Validator.validate_length('store name', 0, 100),
        'zipcode' : Validator.validate_numeric_format(key_name='zipcode'),
    }
    __indexes__ = [
        [
            ("name", pymongo.HASHED),
        ]
    ]

    def response_json(self, excludes=['_id']):
        d = {}
        for key, val in self.items():
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}


class TimeTable(MongoBase):
    """Time table data model.

    table = 
        {
            '1': {  # month
                '1': {  # day
                    '0': {  # hour
                        '00': False,  # minutes
                        '30': False,  # minutes
                    },
                    '1': {
                        '00': False,
                        '30': False,
                    },
                    ...
                    '23': {
                        '00': False,
                        '30': False
                    },
                },
                '2': {
                    '0': {
                        '00': False,
                        ...
                    },
                    ...
                },
                ...
                '31': {
                    '0': {
                        ...
                    },
                    ...
                }
            },
            'year': 2021
        }
    """
    __collection__ = 'timetable'
    __structure__ = {
        '_id': ObjectId,
        'organization_id': ObjectId,  # the organization who registered this.
        'item_id': ObjectId,  # the item which this timetable belongs to.
        'label': str,  # the name tag to be told.
        'year': int,  # the year that this table mentions.
        'table': dict,  # time table
    }
    __required_fields__ = ['_id', 'organization_id', 'label', 'year']
    __default_values__ = {
    }
    __validators__ = {
        'table': Validator.validate_timetable()
    }

    def init(self):
        """Initialize TimeTable object.
        """
        self.table = TimeTable.init_table(self.year)

    def set_availability(self, available: bool, month: int, day: int, hour: int, slot: str):
        """Set availability for a (month, day, hour, slot).

        args:
            - available (bool) : True or False
            - month (int) :
            - day (int) : 
            - hour (int) :
            - slot (str) : '00' or '30'
        returns:
            - success (bool) : True if no problem.
        """
        if not str(month) in self.table.keys():
            raise InvalidFormat(
                f'month {month} doesn\'t exist in key of this timetable.'
            )
            return False
        if not str(day) in self.table[str(month)].keys():
            raise InvalidFormat(
                f'day {day} of {month} doesn\'t exist in key of this timetable.'
            )
            return False
        if not str(hour) in self.table[str(month)][str(day)].keys():
            raise InvalidFormat(
                f'hour {hour} of day {month}/{day} doesn\'t exist in key of this timetable.'
            )
            return False
        if not slot in self.table[str(month)][str(day)][str(hour)].keys():
            raise InvalidFormat(
                f'slot {slot} in hour {hour} of the day {month}/{day} doesn\'t exist in key of this timetable.'
            )
            return False
        self.table[str(month)][str(day)][str(hour)][slot] = available
        return True

    def set_regular_availability(
        self, available: bool,
        from_date: datetime.date, to_date: datetime.date,
        from_hour: int, to_hour: int,
        from_slot: str, to_slot: str, weekdays: list):
        """Set availability regularly.

        example: 
            9:00~12:00 every weekdays
            --------------------------- period
            from_date 2021.1.1
            to_date   2021.12.31 
            ----------------------------- time
            from_hour 9 from_slot '00'
            to_hour 12 to_slot '00'
            -------------------------- weekday
            0: Monday, 1: Tuesday, 2: Wednesday,
            3: Thursday, 4: Friday
            ----------------------------------

        args:
            - available (bool) : True or False
            - from_date (datetime.date) :
            - to_date (datetime.date) :
            - from_hour (int) :
            - to_hour (int) :
            - from_slot (str) : '00' or '30'
            - to_slot (str) : '00' or '30'
            - weekdays ([int]) : list of indices of class Weekday ex) [0, 1, 2]
        returns:
            - success (bool) : True if no problem.
        """
        assert self.table, 'imetable must be initialized.'
        assert 'year' in self.table, 'year must be set in the timetable.'

        def daterange(start_date, end_date):
            for n in range(int((end_date - start_date).days)):
                yield start_date + timedelta(n)

        def is_within_time(
            date, hour, slot,
            from_date, from_hour, from_slot,
            to_date, to_hour, to_slot,
            weekdays
        ):
            # check if date is in range
            if not (date >= from_date or date <= to_date):
                return False
            # check if weekday is in range
            weekday = calendar.weekday(date.year, date.month, date.day)
            if not weekday in weekdays: return False
            # check if hour is in range
            if hour > to_hour or hour < from_hour: return False
            # check if slot is not outside (from)
            if hour == from_hour:
                if int(slot) > int(from_slot):
                    # slot is '30', from_slot is '00'
                    return False
                else:
                    return True
            # check if slot is not outside (to)
            if hour == to_hour:
                if int(slot) < int(to_slot):
                    # slot is '30', to_slot is '00'
                    return False
                else:
                    return True
            # otherwise true
            return True

        for date in daterange(from_date, to_date):
            weekday = calendar.weekday(date.year, date.month, date.day)
            if not weekday in weekdays:
                continue
            for hour in range(from_hour, to_hour+1):
                for slot in ['00', '30']:
                    if is_within_time(
                        date, hour, slot,
                        from_date, from_hour, from_slot,
                        to_date, to_hour, to_slot, weekdays):
                        # if in range, set availability true
                        self.set_availability(True, date.month, date.day, hour, slot) 
        return 

    def is_available(self, date: datetime.date, hour, minute):
        assert date.year == self.table['year'], \
            f'you\'re looing up {date.year} but the timetable is {self.table["year"]}\'s.'
        # check if the date, hour are in key
        if not str(date.month) in self.table: return False
        if not str(date.day) in self.table[str(date.month)]: return False
        if not str(hour) in self.table[str(date.month)][str(date.day)]: return False

        # check if the slot is available
        if minute >= 0 and minute < 30:
            lookup_slot = '00'
        else:
            lookup_slot = '30'
        if not lookup_slot in self.table[str(date.month)][str(date.day)][str(hour)]:
            return False
        return self.table[str(date.month)][str(date.day)][str(hour)][lookup_slot]
        

    @classmethod
    def init_table(cls, year: int):
        """Initialize available table.

        returns:
            - table (dict) : initialized time table.
        """
        if not year:
            year = datetime.date.today().year
        table = {'year': year}
        c = calendar.Calendar()
        months = list(range(1, 12+1))
        for month in months:
            days = c.itermonthdays(year=year, month=month)
            d = {}
            for day in days:
                d[str(day)] = {'00': False, '30': False}
            table[str(month)] = d
        return table

    @classmethod
    def to_weekday(year, month, day, return_name=False):
        """Convert y:m:d to weekday.

        0: Monday
        1: Tuesday
        2: Wednesday
        3: Thursday
        4: Friday
        5: Saturday
        6: Sunday

        returns:
            - weekday (int)  # ex) 0 or 'Monday' if return_name=True
        """
        weekday = calendar.weekday(year, month, day)
        if return_name:
            return calendar.day_name[weekday]
        else:
            return weekday


class Item(MongoBase):
    __collection__ = 'item'
    __structure__ = {
        '_id': ObjectId,
        'name': str,  # eg. Whale watching
        'item_type': int,  # eg. ItemType.EXPERIENCE.value
        'price': int,  # eg. 2000
        'description': str,  # eg. Cruise the ship from 7AM to 12AM.

        'lat': float,  # ex) 35.6602
        'lon': float,  # ex) 139.7301

        'store_info_id': ObjectId,  # StoreInfo._id
        'organization_id': ObjectId,  # The organization who registered this item. ex) Organization._id

        # 'start_date': datetime.datetime,  # start date for sell ex) 20210801
        # 'start_time': datetime.datetime,  # start time for sell ex) 12:00
        # 'end_date': datetime.datetime,  # end date for sell ex) 20210831
        # 'end_time': datetime.datetime,  # end time for sell ex) 18:00

        'reservable': bool,
        'time_table_ids': [ObjectId],  # list of TimeTable._id

        'created_member_id': ObjectId,  # _id of the member who created this content  
        'latest_edit_member_id': ObjectId,  # _id of the member who last edited this content  

        'deleted': bool,  # if True, logically deleted

        'created': datetime.datetime,
        'updated': datetime.datetime
    }
    __min_name_length__ = 1
    __max_name_length__ = 30
    __min_description_length__ = 20
    __max_description_length__ = 100
    __required_fields__ = ['_id', 'name', 'type', 'country']
    __default_values__ = {
        'deleted': False
    }
    __validators__ = {
        'name': Validator.validate_length('organization name', 0, 100)
    }
    __indexes__ = [
        [
            ("name", pymongo.HASHED),
        ]
    ]

    def response_json(self, excludes=[]):
        d = {}
        for key, val in self.items():
            if isinstance(val, ObjectId):
                val = str(val)
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}

    @classmethod
    def fetch(cls, organization_id: ObjectId, with_deleted=False, json=True):
        """Fetch all contents of the organization.

        args:
            - organization_id (ObjectId) : 
            - with_deleted (bool) : fetch deleted items if True
            - json (bool) : return by json if True

        returns:
            - contents (list) : list of Content objects
        """
        if with_deleted:
            items = cls.find({'organization_id': organization_id})
        else:
            items = cls.find({'organization_id': organization_id}, {"deleted": {"$ne": True}})
        if json:
            return [c.response_json() for c in items]
        else:
            return items

    @classmethod
    def validate_name_length(cls, name: str):
        if name < cls.__max_name_length__ and name > cls.__min_name_length__:
            return True
        else:
            return False

    @classmethod
    def validate_description_length(cls, description: str):
        if description < cls.__max_description_length__ and description > cls.__min_description_length__:
            return True
        else:
            return False

