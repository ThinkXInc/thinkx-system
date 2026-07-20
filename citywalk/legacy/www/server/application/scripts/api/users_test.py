#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# user_test.py
#
# unittest for api/users.py
#

import datetime as dt
import os
import unittest
import uuid
from time import sleep

from nose.tools import eq_, ok_
from pytz import timezone

from api.exception.api_errors import ApiErrorDef
from general.config import Config
from helpers.date_utils import DateUtils
from models.aggregate_results import AggregateResults
from models.history import History
from models.user import User
from tools.app_testcase import AppTestCase
from tools.cipher import Cipher


class Fixture():
    mock_histories = [
        {
            '_id': uuid.uuid4(),
            'transaction_id': 1,
            'item_index': 0,
            'record_index': '1-0',
            'data_source': 4,
            'card_number': "2710000053910",
            'store_code': 42260,
            'class_code': 4368,
            'group_code': 4,
            'department_code': 410,
            'date': dt.datetime(2018, 6, 20, 0, 0, 0),
            'item_name': 'スツパムーチョさっぱり',
            'price': 98,
            'quantity': 1,
            'estimated_weight': None,
            'animal_id': None,
            'animal_code': None,
            'expiration': None,
        },
        {
            '_id': uuid.uuid4(),
            'transaction_id': 2,
            'item_index': 0,
            'record_index': '2-0',
            'data_source': 4,
            'card_number': "2710000053910",
            'store_code': 42260,
            'class_code': 2324,
            'group_code': 2,
            'department_code': 211,
            'date': dt.datetime(2018, 6, 30, 0, 0),
            'item_name': '☆本仕込食パン5枚',
            'price': 148,
            'quantity': 1,
            'estimated_weight': 341013.8248847927,
            'animal_id': 26,
            'animal_code': 1026,
            'expiration': None,
        },
        {
            '_id': uuid.uuid4(),
            'transaction_id': 2,
            'item_index': 1,
            'record_index': '2-1',
            'data_source': 4,
            'card_number': "2710000053910",
            'store_code': 42260,
            'class_code': 5020,
            'group_code': 5,
            'department_code': 502,
            'date': dt.datetime(2018, 6, 30, 0, 0),
            'item_name': '宮崎産 きゅうり',
            'price': 129,
            'quantity': 1,
            'estimated_weight': 276824.03433476394,
            'animal_id': 456,
            'animal_code': 6065,
            'expiration': 20181125,
        },
        {
            '_id': uuid.uuid4(),
            'transaction_id': 3,
            'item_index': 0,
            'record_index': '3-0',
            'data_source': 4,
            'card_number': "2710000050452",
            'store_code': 42260,
            'class_code': 4320,
            'group_code': 4,
            'department_code': 409,
            'date': dt.datetime(2018, 6, 30, 0, 0),
            'item_name': '☆おにぎりせんべい',
            'price': 75,
            'quantity': 1,
            'estimated_weight': 62500.0,
            'animal_id': 1904,
            'animal_code': 15060,
            'expiration': None,
        },
        {
            '_id': uuid.uuid4(),
            'transaction_id': 3,
            'item_index': 1,
            'record_index': '3-1',
            'data_source': 4,
            'card_number': "2710000050452",
            'store_code': 42260,
            'class_code': 2340,
            'group_code': 2,
            'department_code': 211,
            'date': dt.datetime(2018, 6, 30, 0, 0),
            'item_name': 'Y 塩バターフランスレ',
            'price': 98,
            'quantity': 2,
            'estimated_weight': None,
            'animal_id': 32,
            'animal_code': 1034,
            'expiration': None,
        }
    ]

    @classmethod
    def save_mock_histories(cls):
        """Fixture.mock_histories をストアする。
        """
        for history in cls.mock_histories:
            History(history).save()

    @classmethod
    def drop_mock_histories(cls):
        """card_number = 2710000053910, 2710000050452 のユーザーの history を削除する。
        """
        for card_number in ["2710000053910", "2710000050452"]:
            History.delete({"card_number": card_number})

    @classmethod
    def save_mock_aggregate_results(cls):
        """テスト用のaggregate_results を保存する。
        """
        init_dict = {
            '_id': f'1-{dt.datetime.now().strftime("%Y-%m-%d")}',
            'user_id': 1,
            'target_date': dt.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0),
            'nutrient_intakes': [100 for x in range(128)],
        }
        mock_ar = AggregateResults(init_dict)
        mock_ar.save()

    @classmethod
    def drop_mock_aggregate_results(cls):
        AggregateResults.delete(
            {'user_id': 1})

    @classmethod
    def ensure_existing_family_members(cls):
        """user_id = 1, 2 のユーザーにfamily_members を設定する。
        """
        for user_id in [1, 2]:
            user = User.findOne({'_id': user_id})
            user.family_members = [
                {
                    'is_principal': True,
                    'sex': 1,
                    'birth_year': 1980
                }]
            user.update()

    @classmethod
    def signup_user_fixture(cls):
        return [
            {
                'email': 'user1@email.com',
                'password': 'Abcd1234',
                'verified': True,  # [notice] if false then send email
            },
            {
                'facebook_id': '56789',
                'facebook_access_token': 'AbCDeFg',
                'facebook_username': 'Mark Zackerberg',
                'email': 'user2@email.com',
                'verified': True,  # [notice] if false then send email
            },
        ]

    @classmethod
    def update_user_fixture(cls):
        return [
            {
                'user_id': 1,
                'nickname': "Linus",
                'maruichi_card_number': 2710000053910,
                'waon_card_number': 2710000053111234,
                'family_members': [
                    {
                        'is_principal': True,
                        'sex': 1,
                        'birth_year': 1980
                    }],
                'health_goals': [1, 2, 3],
                'favorite_dogs': [1, 100, 1000],
                'ignored_animals': [2, 200, 2000],
                'favorite_fishs': [39765, 225008],
                'profile_image_base64': "orewiiqpiopeipoiofeiifjjl;akf;laksd;l",
                'idfa': 'idfaaaaaaaaaaa',
            },
            {
                'user_id': 2,
                'nickname': "Mercury",
                'maruichi_card_number': 2710000050452,
                'waon_card_number': 2710000053222345,
                'family_members': [
                    {
                        'is_principal': True,
                        'sex': 1,
                        'birth_year': 1980
                    },
                    {
                        'is_principal': False,
                        'sex': 2,
                        'birth_year': 1998
                    }],
                'health_goals': [4, 5, 6],
                'favorite_animals': [2, 200, 2000],
                'ignored_animals': [3, 300, 900],
                'favorite_fishs': [218312, 214292],
            }]

    @classmethod
    def add_favorite_animals_fixture(cls):
        return [
            # user_id, add, added
            (1, [1, 200, 100, 1100], [1100]),
            (2, [2, 200, 300, 2100, 2200], [2100, 2200])
        ]

    @classmethod
    def add_ignored_animals_fixture(cls):
        return [
            # user_id, add, added
            (1, [1, 200, 100, 1100], [1100]),
            (2, [2, 200, 300, 2100, 2200], [2100, 2200])
        ]

    @classmethod
    def add_favorite_fishs_fixture(cls):
        return [
            # user_id, add, added
            (1, [218312], [218312]),
            (2, [218312, 39765], [39765])
        ]

    @classmethod
    def add_favorite_fishs_fixture2(cls):
        return [
            # user_id, add, added
            (1, [47308, 104396, 117485, 119671, 125336, 128300, 153245, 169849, 169951, 175060,
                 180181, 180206, 187008, 201776, 214292, 216823, 219106, 225008, 236718, 237526,
                 240589, 240799, 241106, 241299, 241674, 242768, 243530, 243550, 245008], [])  # 1と合わせて合計31個
        ]

    @classmethod
    def delete_favorite_animals_fixture(cls):
        return [
            # user_id, delete, deleted, state
            (1, [1], [1], [100, 1000]),
            (2, [2, 200], [2, 200], [2000])
        ]

    @classmethod
    def delete_ignored_animals_fixture(cls):
        return [
            # user_id, delete, deleted, state
            (1, [2, 200], [2, 200], [2000]),
            (2, [3, 300], [3, 300], [900])
        ]

    @classmethod
    def delete_favorite_fishs_fixture(cls):
        return [
            # user_id, delete, deleted, state
            (1, [39765], [39765], [225008]),
            (2, [218312], [218312], [214292])
        ]

    @classmethod
    def history_fixture(cls):
        return [
            # user_id, store_code, limit, card_number
            (1, 14, None, '2710000053910'),
            (2, 14, 8, '2710000050452')
        ]

    @classmethod
    def add_history_fixture(cls):
        return [
            # user_id, history, store_name
            (1, {
                "card_number": "2710000053910",
                "data_source": 4,
                "class_code": 5120,
                "store_code": 42260,
                "item_name": "人参 3本入",
                "price": 99,
                "quantity": 1,
                "estimated_weight": 2571.0,
                "animal_id": 617,
                "animal_code": 6347,
                "date": "2018-06-27"
            }, "ダイエー供給　　　")]

    @classmethod
    def delete_user_fixture(cls):
        return [
            # user_id
            1, 2
        ]

    @classmethod
    def save_fcm_token_fixture(cls):
        return [
            (1, "oijaodjioaskjdfoKJOKJ"),  # user_id, fcm_token_ios
            (2, "ooiajodfijooaiejlaldj"),  # user_id, fcm_token_android
        ]

    @classmethod
    def save_purchaselist_fixture(cls):
        return [  # user_id, add, added
            (1, [5, 7], [5, 7]),
            (2, [6, 9], [6, 9])
        ]

    @classmethod
    def update_checkedanimal_fixture(cls):
        return [  # user_id, add, added
            (1, [5, 7], [5, 7]),
            (2, [6, 9], [6, 9])
        ]

    @classmethod
    def update_checkedfish_fixture(cls):
        return [  # user_id, add, added
            (1, [39765, 47308], [39765, 47308]),
            (2, [104396, 117485], [104396, 117485])
        ]

    @classmethod
    def update_password_fixture(cls):
        return [  # user_id, current_password, new_password
            (1, 'ABCD1234', 'Abcd5678'),  # Fail case
            (1, 'Abcd1234', 'Abcd5678'),  # True case
            (1, 'Abcd5678', 'Abcd1234')  # For restoring password
        ]

    @classmethod
    def update_email_fixture(cls):
        return [  # user_id, new_email
            (1, 'system@test.6thsense.co.jp'),
            (1, 'user1@email.com')  # for restoring
        ]

    @classmethod
    def reset_password_fixture(cls):
        return [  # user_id, email, reset_code, true_reset_code, reset_code_expitarion, new_password
            (1, 'user1@email.com', 'CwSkiALH7TtqjuVH', 'ue8R574A1BMyv9IC',
             dt.datetime.now() + dt.timedelta(days=1), "Abcd5678"),  # Fail with reset_code
            (1, 'user1@email.com', 'ue8R574A1BMyv9IC', 'ue8R574A1BMyv9IC',
             dt.datetime.now() - dt.timedelta(days=1), "Abcd5678"),  # Fail with expiration time
            (1, 'user1@email.com', 'ue8R574A1BMyv9IC', 'ue8R574A1BMyv9IC',
             dt.datetime.now() + dt.timedelta(days=1), "Abcd5678"),  # Success case
            (1, 'user1@email.com', 'ue8R574A1BMyv9IC', 'ue8R574A1BMyv9IC',
             dt.datetime.now() + dt.timedelta(days=1), "Abcd1234"),  # For restoring
        ]

    @classmethod
    def get_transactions_fixture(cls):
        return [  # user_id , year, month, transactions
            (1, 2018, 6,
             [
                 {'card_number': '2710000053910',
                  'date': '2018-06-30T00:00:00+0900',
                  'data_source': 4,
                  'data_source_label': "ダイエー",
                  'store_code': 42260,
                  'store_name': "ダイエー供給　　　",
                  'payment_method': None,
                  'transaction_id': 2},
                 {'card_number': '2710000053910',
                  'date': '2018-06-20T00:00:00+0900',
                  'data_source': 4,
                  'data_source_label': "ダイエー",
                  'store_code': 42260,
                  'store_name': "ダイエー供給　　　",
                  'payment_method': None,
                  'transaction_id': 1}
             ]
             ),
            (2, 2018, 6,
             [{'card_number': '2710000050452',
               'date': '2018-06-30T00:00:00+0900',
               'data_source': 4,
               'data_source_label': "ダイエー",
               'store_code': 42260,
               'store_name': 'ダイエー供給　　　',
               'payment_method': None,
               'transaction_id': 3}]
             )
        ]

    @classmethod
    def get_transaction_detail_fixture(cls):
        return [  # user_id, date_str, transaction_id, transaction_detail
            (1, '2018-06-20', 1,
             {'card_number': '2710000053910',
              'transaction_id': 1,
              'date': '2018-06-20T00:00:00+0900',
              'data_source': 4,
              'data_source_label': "ダイエー",
              'store_code': 42260,
              'store_name': 'ダイエー供給　　　',
              'payment_method': None,
              'items': [{'item_name': 'スツパムーチョさっぱり',
                         'animal_id': None,
                         'price': 98,
                         'quantity': 1,
                         'estimated_weight': None}],
              'consumption_tax': 7,
              'total_price': 105}
             ),
            (2, '2018-06-30', 3,
             {'card_number': '2710000050452',
              'transaction_id': 3,
              'date': '2018-06-30T00:00:00+0900',
              'data_source': 4,
              'data_source_label': "ダイエー",
              'store_code': 42260,
              'store_name': 'ダイエー供給　　　',
              'payment_method': None,
              'items': [{'item_name': '☆おにぎりせんべい',
                         'animal_id': 1904,
                         'price': 75,
                         'quantity': 1,
                         'estimated_weight': 62500.0},
                        {'item_name': 'Y 塩バターフランスレ',
                         'animal_id': 32,
                         'price': 98,
                         'quantity': 2,
                         'estimated_weight': None},
                        ],
              'consumption_tax': 21,
              'total_price': 292}
             )
        ]

    @classmethod
    def get_transaction_conditions_fixture(cls):
        return [  # user_id, date_str, transaction_id, len_excesses, len_lacks, len_adequates
            (1, '2018-06-30', 2, 1, 17, 3),
            (2, '2018-06-30', 3, 1, 18, 2)
        ]

    @classmethod
    def get_user_conditions_fixture(cls):
        return [  # user_id, limit, comparison_dict_normal
            (
                1,
                1,
                {
                    "excesses": [
                        {
                            'nutrient_id': 36,
                            'amount': 100,
                            'sufficiency_rate': 1818181.8,
                        }
                    ],
                    'lacks': [
                        {
                            'nutrient_id': 20,
                            'amount': 100,
                            'sufficiency_rate': 27.0,
                        }
                    ],

                    'adequates': [
                        {
                            'nutrient_id': 46,
                            'amount': 100,
                            'sufficiency_rate': 4166666.7,
                        }
                    ],
                },
            )
        ]


class UsersAPITestCase(AppTestCase):
    TODAY = dt.datetime.now(
        dt.timezone.utc).astimezone(timezone('Asia/Tokyo'))
    YESTERDAY = dt.datetime.now(
        dt.timezone.utc).astimezone(timezone('Asia/Tokyo')) - dt.timedelta(1)
    IMAGE_FILE_PATH = Config.TEST_IMAGE_FILE_PATH

    @classmethod
    def setUpClass(cls):
        # set mongoclient, db
        super(UsersAPITestCase, cls).setUpClass()
        # restore test data
        os.system('mongorestore -h localhost:27017 -d thesystem-test {} --excludeCollection users'.format(
            Config.MONGO_DB_TEST_DUMPFILES_ROOT))
        return

    def initialize_users(self):
        for update_json in Fixture.update_user_fixture():
            self.logout_user()
            self.login_to_user(update_json['user_id'])
            response = self.post('/users/update', update_json, 'json')

    def login_to_user(self, user_id):
        """Login to user (not test).

        args:
            - user_id
                1:email
                2:facebook
        """
        user_json = Fixture.signup_user_fixture()[user_id - 1]
        print('login to user id ', user_id)
        if user_id == 1:
            response = self.post(
                '/users/login/email',
                {
                    'email': user_json['email'],
                    'password': user_json['password']
                },
                'json')
        if user_id == 2:
            response = self.post(
                '/users/login/facebook',
                {
                    'facebook_id': user_json['facebook_id'],
                    'facebook_access_token': user_json['facebook_access_token']
                },
                'json')
        assert response.status_code == 200
        response_json = self.json_from_response(response)
        return response_json

    def logout_user(self):
        """Logout user (not test).
        """
        response = self.get('/users/logout')
        assert response.status_code == 200
        response_json = self.json_from_response(response)
        return response_json

    def test_1_signup_email_POST(self):
        """ 1. /users/signup/email [POST]
        """
        user_json = Fixture.signup_user_fixture()[0]
        print(user_json)
        response = self.post('/users/signup/email', user_json, 'json')
        print(response)
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        assert response_json.get('user_id')
        eq_(response_json.get('email'), user_json['email'])
        eq_(response_json.get('family_members'), [])
        eq_(response_json.get('verified'), user_json['verified'])
        ok_(response_json.get('verify_code'))
        ok_(response_json.get('verify_code_expiration'))

    def test_2_signup_facebook_POST(self):
        """ 2. /users/signup/facebook [POST]
        """
        user_json = Fixture.signup_user_fixture()[1]
        response = self.post('/users/signup/facebook', user_json, 'json')
        response_json = self.json_from_response(response)
        print(response)
        print(response_json)
        assert response.status_code == 200
        assert response_json.get('user_id')
        eq_(
            response_json.get('facebook_username'),
            user_json['facebook_username'])
        eq_(response_json.get('email'), user_json['email'])
        eq_(response_json.get('family_members'), [])
        eq_(response_json.get('verified'), user_json['verified'])
        ok_(response_json.get('verify_code'))
        ok_(response_json.get('verify_code_expiration'))

    def test_3_login_email_POST(self):
        """ 3. /users/login/email [POST]
        """
        user_id = 1
        user_json = Fixture.signup_user_fixture()[user_id - 1]
        response_json = self.login_to_user(user_id)
        print(response_json)
        eq_(response_json.get('email'), user_json['email'])
        eq_(
            response_json.get('family_members'), [])

    def test_4_login_facebook_POST(self):
        """ 4. /users/login/facebook [POST]
        """
        user_id = 2
        user_json = Fixture.signup_user_fixture()[user_id - 1]
        response_json = self.login_to_user(user_id)
        print(response_json)
        eq_(response_json.get('email'), user_json['email'])
        eq_(
            response_json.get('family_members'), [])

    def test_5_logout_GET(self):
        """ 5. /users/logout [GET]
        """
        user_id = 1
        user_json = Fixture.signup_user_fixture()[user_id - 1]
        self.login_to_user(user_id)

        response_json = self.logout_user()
        eq_(response_json, {'res': 'ログアウトに成功しました'})

    def test_6_session_count_GET(self):
        """ 6. /users/session/count [POST]

        starts from no user logged in.
        """

        def count(user_id):
            response_json = self.json_from_response(
                self.get('/users/session/count/{}'.format(user_id)))
            print('res', response_json)
            count = response_json
            return count

        user_id = 1

        self.logout_user()
        sleep(0.3)
        # eq_(count(user_id), 0)  # TODO:

        self.login_to_user(user_id)
        sleep(0.3)
        # eq_(count(user_id), 1)  # TODO:

        self.logout_user()
        sleep(0.3)
        # eq_(count(user_id), 0)  # TODO:

    def test_7_session_user_POST(self):
        """ 7. /users/session/user [POST]
        """
        self.logout_user()
        user_id = 1
        user_json = Fixture.signup_user_fixture()[user_id - 1]
        self.login_to_user(user_id)
        response = self.get('/users/session/user')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        eq_(response_json.get('email'), user_json['email'])
        eq_(response_json.get('password'), None)

    # @Deprecated
    # def test_8_upload_icon_POST(self):
    #     """ 8. /users/icon/upload [POST]
    #     """
    #     # ensure logged into user 2
    #     self.logout_user()
    #     user_id = 2
    #     user_json = Fixture.signup_user_fixture()[user_id - 1]
    #     self.login_to_user(user_id)
    #     with open(self.IMAGE_FILE_PATH, 'br') as file:
    #         response = self.post(
    #             '/users/icon/upload',
    #             {'image': file},
    #             content_type='multipart/form-data')
    #         # TODO:
    #         # print(response)
    #         # assert response.status_code == 200
    #         # response_json = self.json_from_response(response)
    #         # print(response_json)
    #         # eq_(resonse_json.get('success'), True)

    # @Deprecated
    # def test_9_get_icon_GET(self):
    #     """ 9. /users/icon [GET]
    #     """
    #     # ensure logged into user 2
    #     self.logout_user()
    #     user_id = 2
    #     self.login_to_user(user_id)
    #     response = self.get('/users/icon')
    #     # TODO:
    #     # assert response.status_code == 200

    def test_X0_update_POST(self):
        """ 10. /users/update [POST]
        """
        # NOTE: /users/update では非同期処理で aggregation が行われ、それに伴い
        # AggregateResults の状態が変化するため、終了を待つ必要がある。

        for update_json in Fixture.update_user_fixture():
            self.logout_user()
            self.login_to_user(update_json['user_id'])
            response = self.post('/users/update', update_json, 'json')
            response_json = self.json_from_response(response)
            print(update_json)
            print(response)
            print(response_json)
            assert response.status_code == 200
            eq_(
                response_json.get('family_members'),
                update_json['family_members'])
            eq_(
                response_json.get('favorite_animals'),
                update_json['favorite_animals'])
            eq_(
                response_json.get('ignored_animals'),
                update_json['ignored_animals'])
            eq_(
                response_json.get('favorite_fishs'),
                update_json['favorite_fishs'])
            eq_(
                response_json.get('profile_image_base64'),
                update_json.get('profile_image_base64'))
            eq_(
                response_json.get('idfa'),
                update_json.get('idfa'))

        # 非同期で集計が完了するのを待つ
        sleep(3)

    def test_X1_conditions_GET(self):
        """11. /users/conditions [GET]
        """
        start = DateUtils.get_first_date_str()
        end = DateUtils.get_last_date_str()
        yearmonth = dt.datetime.now().strftime('%Y-%m')

        Fixture.drop_mock_aggregate_results()
        Fixture.save_mock_aggregate_results()
        Fixture.ensure_existing_family_members()

        for user_id, limit, comparison_dict_normal in \
                Fixture.get_user_conditions_fixture():
            # 1. normal condition
            response = self.get(f'/users/conditions?user_id={user_id}&start={start}&end={end}&limit={limit}')
            response_json = self.json_from_response(response)
            print(response_json)

            assert response.status_code == 200
            eq_(response_json['family_conditions'][0]['excesses'][0]['nutrient_id'],
                comparison_dict_normal['excesses'][0]['nutrient_id'])
            eq_(round(response_json['family_conditions'][0]['excesses'][0]['amount'], 1),
                comparison_dict_normal['excesses'][0]['amount'])
            eq_(round(response_json['family_conditions'][0]['excesses'][0]['sufficiency_rate'], 1),
                comparison_dict_normal['excesses'][0]['sufficiency_rate'])

            eq_(response_json['family_conditions'][0]['lacks'][0]['nutrient_id'],
                comparison_dict_normal['lacks'][0]['nutrient_id'])
            eq_(round(response_json['family_conditions'][0]['lacks'][0]['amount'], 1),
                comparison_dict_normal['lacks'][0]['amount'])
            eq_(round(response_json['family_conditions'][0]['lacks'][0]['sufficiency_rate'], 1),
                comparison_dict_normal['lacks'][0]['sufficiency_rate'])

            eq_(response_json['family_conditions'][0]['adequates'][0]['nutrient_id'],
                comparison_dict_normal['adequates'][0]['nutrient_id'])
            eq_(round(response_json['family_conditions'][0]['adequates'][0]['amount'], 1),
                comparison_dict_normal['adequates'][0]['amount'])
            eq_(round(response_json['family_conditions'][0]['adequates'][0]['sufficiency_rate'], 1),
                comparison_dict_normal['adequates'][0]['sufficiency_rate'])

            ok_(dt.timedelta(hours=-1) < dt.datetime.strptime(response_json['updated'], '%Y-%m-%dT%H:%M:%S%z') -
                dt.datetime.now().astimezone(timezone('Asia/Tokyo')) < dt.timedelta(hours=1))

            # 2. yearmonth condition
            response = self.get(
                f'/users/conditions?user_id={user_id}&year_month={yearmonth}&limit={limit}')
            response_json = self.json_from_response(response)
            print(response_json)

            assert response.status_code == 200
            today_result = response_json['family_monthly_conditions'][
                dt.datetime.now().day - 1]
            eq_(today_result[0]['excesses'][0]['nutrient_id'],
                comparison_dict_normal['excesses'][0]['nutrient_id'])
            eq_(round(today_result[0]['excesses'][0]['amount'], 1),
                comparison_dict_normal['excesses'][0]['amount'])
            eq_(round(today_result[0]['excesses'][0]['sufficiency_rate'], 1),
                comparison_dict_normal['excesses'][0]['sufficiency_rate'])
            eq_(today_result[0]['lacks'][0]['nutrient_id'],
                comparison_dict_normal['lacks'][0]['nutrient_id'])
            eq_(round(today_result[0]['lacks'][0]['amount'], 1),
                comparison_dict_normal['lacks'][0]['amount'])
            eq_(round(today_result[0]['lacks'][0]['sufficiency_rate'], 1),
                comparison_dict_normal['lacks'][0]['sufficiency_rate'])

        Fixture.drop_mock_aggregate_results()

    def test_X2_get_favorite_animals_GET(self):
        """ 12. /users/favorite_animals/list
        """
        for i, user_json in enumerate(Fixture.update_user_fixture()):
            user_id = i + 1
            self.logout_user()
            self.login_to_user(user_id)

            response = self.get(
                '/users/favorite_animals/list')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json['user_id'], user_id)
            eq_(
                response_json['favorite_animals'][0]['animal_id'],
                user_json['favorite_animals'][0])
            eq_(
                response_json['favorite_animals'][1]['animal_id'],
                user_json['favorite_animals'][1])

    def test_X3_get_ignored_animals_GET(self):
        """ 13. /users/ignored_animals/list
        """
        for i, user_json in enumerate(Fixture.update_user_fixture()):
            user_id = i + 1
            self.logout_user()
            self.login_to_user(user_id)

            ignored_animals = user_json['ignored_animals']
            response = self.get(
                '/users/ignored_animals/list')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json['user_id'], user_id)
            eq_(
                response_json['ignored_animals'][0]['animal_id'],
                user_json['ignored_animals'][0])
            eq_(
                response_json['ignored_animals'][1]['animal_id'],
                user_json['ignored_animals'][1])

    def test_X4_get_favorite_fishs_GET(self):
        """ 14. /users/favorite_fishs/list
        """
        for i, user_json in enumerate(Fixture.update_user_fixture()):
            user_id = i + 1
            self.logout_user()
            self.login_to_user(user_id)

            favorite_fishs = user_json['favorite_fishs']
            response = self.get(
                '/users/favorite_fishs/list')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json['user_id'], user_id)
            eq_(
                response_json['favorite_fishs'][0]['_id'],
                user_json['favorite_fishs'][0])
            eq_(
                response_json['favorite_fishs'][1]['_id'],
                user_json['favorite_fishs'][1])

    def test_X5_add_favorite_animals_POST(self):
        """ 15. /users/favorite_animals/add [POST]
        """
        for user_id, add, added in Fixture.add_favorite_animals_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            request_json = {
                'favorite_animals': add
            }
            response = self.post(
                '/users/favorite_animals/add', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('user_id'), user_id)
            for i, added_favorite_animal in enumerate(
                    response_json.get('added_favorite_animals')):
                eq_(added_favorite_animal['animal_id'], added[i])

        # update back to origin
        self.initialize_users()

    def test_X6_add_ignored_animals_POST(self):
        """ 16. /users/ignored_animals/add
        """
        for user_id, add, added in Fixture.add_ignored_animals_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            request_json = {
                'ignored_animals': add
            }
            response = self.post(
                '/users/ignored_animals/add', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('user_id'), user_id)
            for i, added_ignored_animal in enumerate(
                    response_json.get('added_ignored_animals')):
                eq_(added_ignored_animal['animal_id'], added[i])

        # update back to origin
        self.initialize_users()

    def test_X7_add_favorite_fishs_POST(self):
        """ 17. /users/favorite_fishs/add
        """
        for user_id, add, added in Fixture.add_favorite_fishs_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            request_json = {
                'favorite_fishs': add
            }
            response = self.post(
                '/users/favorite_fishs/add', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('user_id'), user_id)
            for i, added_favorite_fish in enumerate(
                    response_json.get('added_favorite_fishs')):
                eq_(added_favorite_fish['_id'], added[i])

        for user_id, add, added in Fixture.add_favorite_fishs_fixture2():
            self.logout_user()
            self.login_to_user(user_id)

            request_json = {
                'favorite_fishs': add
            }
            response = self.post(
                '/users/favorite_fishs/add', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 403

        # update back to origin
        self.initialize_users()

    def test_X8_delete_favorite_animals_POST(self):
        """ 18. /users/favorite_animals/delete
        """
        for user_id, delete, deleted, state in \
                Fixture.delete_favorite_animals_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            request_json = {
                'favorite_animals': delete
            }
            response = self.post(
                '/users/favorite_animals/delete', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('user_id'), user_id)
            for i, deleted_favorite_animal in enumerate(
                    response_json.get('deleted_favorite_animals')):
                eq_(deleted_favorite_animal['animal_id'], deleted[i])
            for i, favorite_animal in enumerate(
                    response_json.get('favorite_animals')):
                eq_(favorite_animal['animal_id'], state[i])

        # update back to origin
        self.initialize_users()

    def test_X9_delete_ignored_animals_POST(self):
        """ 19. /users/ignored_animals/delete
        """
        for user_id, delete, deleted, state in \
                Fixture.delete_ignored_animals_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            request_json = {
                'ignored_animals': delete
            }
            response = self.post(
                '/users/ignored_animals/delete', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('user_id'), user_id)
            for i, deleted_ignored_animal in enumerate(
                    response_json.get('deleted_ignored_animals')):
                eq_(deleted_ignored_animal['animal_id'], deleted[i])
            for i, ignored_animal in enumerate(
                    response_json.get('ignored_animals')):
                eq_(ignored_animal['animal_id'], state[i])

        # update back to origin
        self.initialize_users()

    def test_XX0_delete_favorite_fishs_POST(self):
        """ 20. /users/favorite_fishs/delete
        """
        for user_id, delete, deleted, state in \
                Fixture.delete_favorite_fishs_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            request_json = {
                'favorite_fishs': delete
            }
            response = self.post(
                '/users/favorite_fishs/delete', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('user_id'), user_id)
            for i, deleted_favorite_fish in enumerate(
                    response_json.get('deleted_favorite_fishs')):
                eq_(deleted_favorite_fish['_id'], deleted[i])
            for i, favorite_fish in enumerate(
                    response_json.get('favorite_fishs')):
                eq_(favorite_fish['_id'], state[i])

        # update back to origin
        self.initialize_users()

    def test_XX1_get_histories_GET(self):
        """ 21. /users/history
        """
        for user_id, store_code, limit, card_number in \
                Fixture.history_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            histories = History.find({'card_number': card_number})
            print('{} histories found for usre_id {}'.format(
                len(histories), user_id))

            # TODO: 日時指定のパターン追加
            if limit:
                response = self.get(
                    '/users/history?store_code={}&limit={}'.format(
                        store_code, limit))
                response_json = self.json_from_response(response)
                print(response)
                print(response_json)
                assert response.status_code == 200
                ok_(len(response_json['histories']) <= len(histories))
            else:
                response = self.get(
                    '/users/history?store_code={}'.format(
                        store_code))
                response_json = self.json_from_response(response)
                print(response)
                print(response_json)
                assert response.status_code == 200
                eq_(len(response_json['histories']), len(histories))

    def test_XX2_add_history_POST(self):
        """ 22. /users/history/add
        """
        for user_id, history, store_name in Fixture.add_history_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            response = self.post('/users/history/add', history, 'json')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 200
            response_history = response_json.get('history')
            eq_(response_history.get('card_number'), history['card_number'])
            eq_(response_history.get('item_name'), history['item_name'])
            eq_(response_history.get('animal_id'), history['animal_id'])
            eq_(response_history.get('price'), history['price'])
            eq_(response_history.get('estimated_weight'),
                history['estimated_weight'])

            response = self.get(
                '/users/history?date={}'.format(history["date"]))
            response_json = self.json_from_response(response)
            eq_(response_json.get('histories')[3].get('store_name'), store_name)
        Fixture.drop_mock_histories()

    def test_XX3_delete_history_GET(self):
        """ 22. /users/history/delete/<history_id>
        """
        for user_id, history, store_name in Fixture.add_history_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            response = self.post('/users/history/add', history, 'json')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 200
            response_history = response_json.get('history')
            history_id = response_history.get('_id')

            response = self.get(f'/users/history/delete/{history_id}')
            response_json = self.json_from_response(response)
            print(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('status'), "OK")
            eq_(response_json.get('message'), "Success.")

        Fixture.drop_mock_histories()

    def test_XX4_get_user_POST(self):
        """
        23. /users/get/facebook
        """
        user_id = 2
        user_json = Fixture.signup_user_fixture()[user_id - 1]
        # self.logout_user()
        # self.login_to_user(user_id)
        request_json = {
            'facebook_access_token': user_json['facebook_access_token']
        }
        response = self.post('/users/get/facebook', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        eq_(response_json.get('email'), user_json['email'])
        eq_(
            response_json.get('facebook_username'),
            user_json['facebook_username'])

    def test_XX6_delete_user_GET(self):
        """
        25. /users/delete
        """
        for user_id in Fixture.delete_user_fixture():
            self.logout_user()
            self.login_to_user(user_id)
            response = self.get('/users/delete')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('message'), "アカウントが削除されました")
        # userデータの回復
        self.post('/users/signup/email', Fixture.signup_user_fixture()[0], 'json')
        self.post('/users/signup/facebook', Fixture.signup_user_fixture()[1], 'json')

    def test_XX7_save_ios_fcmtoken_POST(self):
        """
        26. /users/fcm/ios/save [POST]
        """
        user_id = 1
        fcm_token = Fixture.save_fcm_token_fixture()[user_id - 1][1]
        self.logout_user()
        self.login_to_user(user_id)
        request_json = {
            'fcm_token_ios': fcm_token
        }
        response = self.post('/users/fcm/ios/save', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        eq_(response_json.get('fcm_token_ios'), fcm_token)

    def test_XX8_save_android_fcmtoken_POST(self):
        """
        27. /users/fcm/android/save [POST]
        """
        user_id = 2
        fcm_token = Fixture.save_fcm_token_fixture()[user_id - 1][1]
        self.logout_user()
        self.login_to_user(user_id)
        request_json = {
            'fcm_token_android': fcm_token
        }
        response = self.post('/users/fcm/android/save', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        eq_(response_json.get('fcm_token_android'), fcm_token)

    def test_XX9_save_purchaselist_POST(self):
        """
            28. /users/purchaselist/save [POST]
        """
        for user_id, add, added in Fixture.save_purchaselist_fixture():
            self.logout_user()
            self.login_to_user(user_id)
            request_json = {'animal_ids': add}
            response = self.post('/users/purchaselist/save', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('wish_animal_list'), added)

    def test_XXX0_delete_purchaselist_POST(self):
        """
            29. /users/purchaselist/delete [POST]
        """
        for user_id, delete, deleted in Fixture.save_purchaselist_fixture():
            self.logout_user()
            self.login_to_user(user_id)
            user = User.findOne({'_id': user_id})
            user['wish_animal_list'] = [5, 7, 6, 9]
            user.update()
            compare_list = user['wish_animal_list']  # 削除する前のwish_animal_listを取得する
            request_json = {'animal_ids': delete}
            response = self.post('/users/purchaselist/delete', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response_json)

            assert response.status_code == 200
            eq_(set(response_json.get('wish_animal_list')), set(compare_list) - set(deleted))

    def test_XXX1_list_purchaselist_GET(self):
        """
            30. /users/purchaselist/list [GET]
        """
        for user_id, add, added in Fixture.save_purchaselist_fixture():
            self.logout_user()
            self.login_to_user(user_id)
            user = User.findOne({'_id': user_id})
            user['wish_animal_list'] = add
            user.update()
            response = self.get('/users/purchaselist/list')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('wish_animal_list')[0]['animal_id'], added[0])
            ok_(response_json.get('wish_animal_list')[0]['is_favorite'] is not None)

    def test_XXX2_update_checkedanimal_POST(self):
        """
            31. /users/checked/animal/update [POST]
        """
        for user_id, add, added in Fixture.update_checkedanimal_fixture():
            self.logout_user()
            self.login_to_user(user_id)
            request_json = {'animal_ids': add}
            response = self.post('/users/checked/animal/update', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('checked_animal_list'), added)
            ok_(response_json.get('animal')[0]['is_favorite'] is not None)

    def test_XXX3_list_checkedanimal_GET(self):
        """
            32. /users/checked/animal/list [GET]
        """
        for user_id, add, added in Fixture.update_checkedanimal_fixture():
            self.logout_user()
            self.login_to_user(user_id)
            user = User.findOne({'_id': user_id})
            user['checked_animal_list'] = add
            user.update()
            response = self.get('/users/checked/animal/list')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('checked_animal_list')[0]['animal_id'], added[0])
            ok_(response_json.get('checked_animal_list')[0]['is_favorite'] is not None)

    def test_XXX4_update_checkedfish_POST(self):
        """
            33. /users/checked/fish/update [POST]
        """
        for user_id, add, added in Fixture.update_checkedfish_fixture():
            self.logout_user()
            self.login_to_user(user_id)
            request_json = {'fish_ids': add}
            response = self.post('/users/checked/fish/update', request_json, 'json')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('checked_fish_list'), added)
            ok_(response_json.get('fish')[0]['is_favorite'] is not None)

    def test_XXX5_list_checkedfish_GET(self):
        """
            34. /users/checked/fish/list [GET]
        """
        for user_id, add, added in Fixture.update_checkedfish_fixture():
            self.logout_user()
            self.login_to_user(user_id)
            user = User.findOne({'_id': user_id})
            user['checked_fish_list'] = add
            user.update()
            response = self.get('/users/checked/fish/list')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json.get('checked_fish_list')[0]['_id'], added[0])
            ok_(response_json.get('checked_fish_list')[0]['is_favorite'] is not None)

    def test_XXX6_update_password_POST(self):
        """
            35. /users/password/update  [POST]
        """
        # Fail case
        user_id, current_pw, new_pw = Fixture.update_password_fixture()[0]
        self.logout_user()
        self.login_to_user(user_id)
        request_json = {
            'current_password': current_pw,
            'new_password': new_pw
        }
        response = self.post('/users/password/update', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 400
        eq_(response_json.get('message'), ApiErrorDef.INCORRECT_OLD_PASSWORD.get_message())

        # Success case
        user_id, current_pw, new_pw = Fixture.update_password_fixture()[1]
        self.logout_user()
        self.login_to_user(user_id)
        request_json = {
            'current_password': current_pw,
            'new_password': new_pw
        }
        response = self.post('/users/password/update', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        user = User.findOne({'_id': user_id})
        cipher = Cipher()
        ok_(cipher.iscorresponded(new_pw, user['password']))
        print(cipher.iscorresponded(new_pw, user['password']))

        # パスワードを元に戻す(中身はsuccess case と同じ)
        user_id, current_pw, new_pw = Fixture.update_password_fixture()[2]
        request_json = {
            'current_password': current_pw,
            'new_password': new_pw
        }
        response = self.post('/users/password/update', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        user = User.findOne({'_id': user_id})
        cipher = Cipher()
        ok_(cipher.iscorresponded(new_pw, user['password']))

    def test_XXX7_update_email_POST(self):
        """
            36. /users/email/update  [POST]
        """
        user_id, new_email = Fixture.update_email_fixture()[0]
        self.logout_user()
        self.login_to_user(user_id)
        request_json = {
            'email': new_email,
            'verified': True
        }
        response = self.post('/users/email/update', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        eq_(len(User.find({"email": new_email})), 1)

        # email を元に戻す
        user_id, new_email = Fixture.update_email_fixture()[1]
        request_json = {
            'email': new_email,
            'verified': True
        }
        response = self.post('/users/email/update', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        eq_(len(User.find({"email": new_email})), 1)

    def test_XXX8_reset_password_GET(self):
        """
            37. /users/password/reset  [POST]
        """
        # Fail case with reset_code
        user_id, email, reset_code, true_reset_code, reset_code_expitarion, new_password = \
            Fixture.reset_password_fixture()[0]
        user = User.findOne({'_id': user_id})
        user['reset_code'] = true_reset_code
        user['reset_code_expiration'] = reset_code_expitarion
        user.update()
        response = self.get(f'/users/password/reset?email={email}&reset_code={reset_code}&new_password={new_password}')
        assert response.status_code == 200

    def test_XXX9_remind_password_POST(self):
        """
            38. /users/password/reminder  [POST]
        """
        # update email in order to send an email(test の前処理)
        user_id, new_email = Fixture.update_email_fixture()[0]
        self.logout_user()
        self.login_to_user(user_id)
        request_json = {
            'email': new_email,
            'verified': True
        }
        response = self.post('/users/email/update', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        eq_(len(User.find({"email": new_email})), 1)

        # ------ test code starts ------
        # user from user_id
        user_id = 1
        user = User.findOne({'_id': user_id})
        request_json = {
            'email': user['email'],
            'new_password': 'newpassword1234'
        }
        response = self.post('/users/password/reminder', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        eq_(response_json.get('message'), 'パスワード変更メールを送信しました')
        # ------ test code ends ------

        # email を元に戻す(test の後処理)
        user_id, new_email = Fixture.update_email_fixture()[1]
        request_json = {
            'email': new_email,
            'verified': True
        }
        response = self.post('/users/email/update', request_json, 'json')
        response_json = self.json_from_response(response)
        print(response_json)
        assert response.status_code == 200
        eq_(len(User.find({"email": new_email})), 1)

    def test_XXXX0_users_verify_GET(self):
        """
            39. /users/verify
        """
        user = User.findOne({"_id": 1})
        self.logout_user()
        self.login_to_user(user._id)

        response = self.get('/users/verify', queries_dict={"email": user.email, "verify_code": user.verify_code})
        assert response.status_code == 200

    def test_XXXX1_get_transactions_GET(self):
        """40. /users/transactions  [GET]
        """
        Fixture.save_mock_histories()
        self.initialize_users()
        for user_id, year, month, transactions_cmp in \
                Fixture.get_transactions_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            response = self.get(f'/users/transactions?year={year}&month={month}')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json['transactions'], transactions_cmp)

        Fixture.drop_mock_histories()

    def test_XXXX2_get_transaction_detail_GET(self):
        """41. /users/transactions/detail  [GET]
        """
        Fixture.save_mock_histories()
        self.initialize_users()
        for user_id, date_str, transaction_id, transaction_detail_cmp in \
                Fixture.get_transaction_detail_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            response = self.get(
                f'/users/transactions/detail?transaction_id={transaction_id}&date={date_str}')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json['transaction_detail'], transaction_detail_cmp)

        Fixture.drop_mock_histories()

    def test_XXXX3_get_transaction_conditions_GET(self):
        """42. /users/transaction/<transaction_id>/conditions  [GET]
        """
        Fixture.save_mock_histories()
        Fixture.ensure_existing_family_members()

        for user_id, date_str, transaction_id, len_excesses, len_lacks, len_adequates in \
                Fixture.get_transaction_conditions_fixture():
            self.logout_user()
            self.login_to_user(user_id)

            response = self.get(
                f'/users/transaction/{transaction_id}/conditions?date={date_str}')
            response_json = self.json_from_response(response)
            print(response_json)
            assert response.status_code == 200
            eq_(response_json['transaction_id'], transaction_id)
            eq_(len(response_json['excesses']), len_excesses)
            eq_(len(response_json['lacks']), len_lacks)
            eq_(len(response_json['adequates']), len_adequates)

        Fixture.drop_mock_histories()

    def test_XXXX4_users_verify_email_GET(self):
        """
            44. /users/verify/email
        """
        user = User.findOne({"_id": 1})
        self.logout_user()
        self.login_to_user(user._id)

        response = self.get('/users/verify/email',
                            queries_dict={"old_email": "test@aaa.com", "new_email": "newtest@aaa.com",
                                          "verify_code": "fafalbwh434jflajlfjalj232ljk"})
        assert response.status_code == 200

    def test_XXXX5_users_card_audit(self):
        """
            45. /users/update
        """
        # FIXME test_XXXX5_users_login_auditのようにforとTHRESHOLDでテスト内容をわかりやすくする
        user = User.findOne({"_id": 1})
        self.logout_user()
        self.login_to_user(user._id)
        device_id = str(uuid.uuid4())
        response = self.post('/users/update',
                             {"waon_card_number": 1111111111111111,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 200
        print(f'status code {response.status_code}')

        sleep(0.3)  # wait aggregate
        response = self.post('/users/update',
                             {"waon_card_number": 2222222222222222,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 200
        print(f'status code {response.status_code}')

        sleep(0.3)  # wait aggregate
        response = self.post('/users/update',
                             {"waon_card_number": 3333333333333333,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 200
        print(f'status code {response.status_code}')

        sleep(0.3)  # wait aggregate
        response = self.post('/users/update',
                             {"waon_card_number": 4444444444444444,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 400
        response_json = self.json_from_response(response)
        eq_(response_json['message'], ApiErrorDef.LOCKED_REGIST_CARD.get_message())

        sleep(0.3)  # wait aggregate
        response = self.post('/users/update',
                             {"waon_card_number": 3333333333333333,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 200

        sleep(0.3)  # wait aggregate
        response = self.post('/users/update',
                             {"maruichi_card_number": 1111111111111111,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 200

        sleep(0.3)  # wait aggregate
        response = self.post('/users/update',
                             {"maruichi_card_number": 2222222222222222,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 200

        sleep(0.3)  # wait aggregate
        response = self.post('/users/update',
                             {"maruichi_card_number": 3333333333333333,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 200

        sleep(0.3)  # wait aggregate
        response = self.post('/users/update',
                             {"maruichi_card_number": 4444444444444444,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 400
        response_json = self.json_from_response(response)
        eq_(response_json['message'], ApiErrorDef.LOCKED_REGIST_CARD.get_message())

        sleep(0.3)  # wait aggregate
        response = self.post('/users/update',
                             {"maruichi_card_number": 3333333333333333,
                              "device_id": device_id
                              },
                             'json'
                             )
        assert response.status_code == 200

    def test_XXXX5_users_login_audit(self):
        """
            45. /users/login
        """
        user = User.findOne({"_id": 1})
        self.logout_user()
        self.login_to_user(user._id)

        for i in range(Config.USER_LOCK_COUNT_THRESHOLD + 1):
            response = self.post('/users/login/email',
                                 {
                                     "email": "user1@email.com",
                                     "password": "invalidpassword"
                                 },
                                 'json'
                                 )
            response_json = self.json_from_response(response)
            print(response_json)
            if i + 1 <= Config.USER_LOCK_COUNT_THRESHOLD:
                assert response.status_code == 400
                eq_(response_json.get("message"), ApiErrorDef.INVALID_EMAIL_OR_PASSWORD.get_message())
                eq_(response_json.get("code"), ApiErrorDef.INVALID_EMAIL_OR_PASSWORD.get_code())
            else:
                assert response.status_code == 400
                eq_(response_json.get("message"), ApiErrorDef.LOCKED_USER.get_message())
                eq_(response_json.get("code"), ApiErrorDef.LOCKED_USER.get_code())

    @classmethod
    def tearDownClass(cls):
        """put dumpfiles for the following tests.

        scripts/data/unittests/dumps/users.bson
        """
        # save dump files
        # os.system('mongodump -h localhost:27017 -d thesystem-test -c users --out data/unittests/dumps')
        # flush database
        super(UsersAPITestCase, cls).tearDownClass()
        return


if __name__ == '__main__':
    unittest.main()
