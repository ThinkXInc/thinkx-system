#!/usr/local/bin/python
# -*- coding:utf-8 -*-

# NOTE: Ancient code. Move to helpers/dateutils.py

# helpers/date_utils.py
#
# DATEに関する共通処理
# e.g) format %Y-%m-%dT%H:%M:%S%z
#

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta


class DateUtils:
    @staticmethod
    def get_date(str_date=None, format='%Y-%m-%d'):
        """文字列からDateに変換し返却

        str_dateがない場合は現在時刻のdatetimeを返却

        args:
            - str_date: str default None
            - format: str default '%Y-%m-%d'

        returns:
            - date: datetime
        """
        if not str_date:
            return datetime.today()
        return datetime.strptime(str_date, format)

    @staticmethod
    def get_date_str(date=None, format='%Y-%m-%d'):
        """Dateの文字列を返却

        dateがない場合は現在時刻のdate_strを返却

        args:
            - date: datetime default None
            - format: str default '%Y-%m-%d'

        returns:
            - date_str: str # ex) 2018-11-01
        """
        if not date:
            date = datetime.today()
        return datetime.strftime(date, format)

    @staticmethod
    def get_first_date_str(date=None, format='%Y-%m-%d'):
        """月初の文字列を返却

        dateがない場合は現在時刻の月初を返却

        args:
            - date: datetime default None # ex) datetime(2018,12,22,33,44...)
            - format: str default '%Y-%m-%d'

        returns:
            - first_date_str: str # ex) "2018-12-01"
        """
        if not date:
            date = datetime.today()
        first_day = date.replace(day=1)
        return datetime.strftime(first_day, format)

    @staticmethod
    def get_last_date_str(date=None, format='%Y-%m-%d'):
        """月末の文字列を返却

        dateがない場合は現在時刻の月末を返却

        args:
            - date: datetime default None # ex) datetime(2018,12,22,33,44...)
            - format: str default '%Y-%m-%d'

        returns:
            - last_date_str: str # ex) "2018-12-31"
        """
        if not date:
            date = datetime.today()
        last_day = (date + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
        return datetime.strftime(last_day, format)

    @staticmethod
    def get_first_date(date=None):
        """月初のdateを返却

        dateがない場合は現在時刻の月初を返却

        args:
            - date: datetime default None # ex) datetime(2018,12,22,33,44...)

        returns:
            - first_date: datetime # ex) datetime(2018,12,01,00,00...)
        """
        if not date:
            date = datetime.today()
        first_day = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return first_day

    @staticmethod
    def get_last_date(date=None):
        """月末のdateを返却

        dateがない場合は現在時刻の月末を返却

        args:
            - date: datetime default None # ex) datetime(2018,12,22,33,44...)

        returns:
            - first_date: datetime # ex) datetime(2018,12,31,00,00...)
        """
        if not date:
            date = datetime.today()
        last_day = (date + relativedelta(months=1)).replace(day=1, hour=0, minute=0, second=0,
                                                            microsecond=0) - timedelta(days=1)
        return last_day

    @staticmethod
    def get_neutral_date(date=None):
        """時分秒を0に変換し返却する

        dateがない場合は現在時刻の時分秒を0に変換し返却する
        args:
            - date: datetime default None # ex) datetime(2018,12,22,33,44...)

        returns:
            - neutral_date: datetime # ex) datetime(2018,12,22,00,00...)

        """
        if not date:
            date = datetime.today()
        neutral_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return neutral_date

    @staticmethod
    def get_n_months_ago_date(date=None, n_month=1):
        """n月前のdateを返却

        dateがない場合は現在時刻のnヶ月前のdateを返却する

        args:
            - date: datetime default None # ex) datetime(2018,12,22,33,44...)
            - n_month: int default 1

        returns:
            - n_month_ago: datetime # ex) datetime(2018,11,22,33,44...)

        """
        if not date:
            date = datetime.today()
        n_month_ago = date - relativedelta(months=n_month)
        return n_month_ago

    @staticmethod
    def get_n_days_ago_date(date=None, n_days=1):
        """n日前のdateを返却

        dateがない場合は現在時刻のn日前のdateを返却する

        args:
            - date: datetime default None # ex) datetime(2018,12,22,33,44...)
            - n_days: int default 1

        returns:
            - n_days_ago: datetime # ex) datetime(2018,12,21,33,44...)

        """
        if not date:
            date = datetime.today()
        n_days_ago = date - relativedelta(days=n_days)
        return n_days_ago

    @staticmethod
    def get_n_months_after_date(date=None, n_month=1):
        """n月後のdateを返却

        dateがない場合は現在時刻のnヶ月後のdateを返却する

        args:
            - date: datetime default None # ex) datetime(2018,11,22,33,44...)
            - n_month: int default 1

        returns:
            - n_month_after: datetime # ex) datetime(2018,12,22,33,44...)

        """
        if not date:
            date = datetime.today()
        n_month_after = date + relativedelta(months=n_month)
        return n_month_after

    @staticmethod
    def get_n_days_after_date(date=None, n_days=1):
        """n日後のdateを返却

        dateがない場合は現在時刻のn日後のdateを返却する

        args:
            - date: datetime default None # ex) datetime(2018,12,22,33,44...)
            - n_days: int default 1

        returns:
            - n_days_ago: datetime # ex) datetime(2018,12,23,33,44...)

        """
        if not date:
            date = datetime.today()
        n_days_after = date + relativedelta(days=n_days)
        return n_days_after
