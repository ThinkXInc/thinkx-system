#!/usr/bin/env python
# -*- coding: utf-8 -*-

import webapp2
import logging
import datetime
import os
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import mail
from webapp2_extras import sessions

#Host url ==============================
HOST_URL = "http://localhost:8080"
#HOST_URL = "http://www.thinkxinc.com"
# ===========================================
 
##------------------------------------------------------------------------------------------
#webapp2extraのSession機能を付加したRequestHandlerの拡張クラス
#keys.pyにconfig情報を記述してある(最下行でその設定を適用している)
class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()
##---------------------------------------------------------------------------------------


class TopPage(webapp2.RequestHandler):
    def get(self):
		logging.info('TopPage')
		logging.info('welcome with no session')
	 	fpath = os.path.join(os.path.dirname(__file__),'templates','top.html')
	 	self.response.headers['Content-Type'] = 'text/html'
		html = template.render(fpath,None)
	 	self.response.out.write(html)


app = webapp2.WSGIApplication([
    ('/', TopPage)
], debug=True)






""" カーソルインデックス 
#IN または != を使用するクエリではカーソルを使えない
#同じクエリでないとだめ
#複雑なクエリでは同じ結果が２回以上返る場合がある
#開始カーソルのみの使用で、必要件数が分かっている場合はfetch()を使った方が高速
#有効でなくなったカーソルを使用しようとすると、datastore_errors.BadRequestErrorが送出される

# Start a query for all Person entities.
people = Person.all()

# If the app stored cursors during a previous request, use them.
start_cursor = memcache.get('person_start_cursor')
end_cursor = memcache.get('person_end_cursor')
if start_cursor:
    people.with_cursor(start_cursor=start_cursor)
if end_cursor:
    people.with_cursor(end_cursor=end_cursor)

# Iterate over the results.
for person in people:
  # Do something


# カウンターシャード 
#1秒間に5回以上エンティティを更新するには
#カウンターを複数のシャードに分割して統合する

class SimpleCounterShard(db.Model):
    #Shards for the counter
    count = db.IntegerProperty(required=True, default=0)

NUM_SHARDS = 20

def get_count():
    #Retrieve the value for a given sharded counter.
    total = 0
    for counter in SimpleCounterShard.all():
        total += counter.count
    return total

def increment():
    #Increment the value for a given sharded counter.
    def txn():
        index = random.randint(0, NUM_SHARDS - 1)
        shard_name = "shard" + str(index)
        counter = SimpleCounterShard.get_by_key_name(shard_name)
        if counter is None:
            counter = SimpleCounterShard(key_name=shard_name)
        counter.count += 1
        counter.put()
    db.run_in_transaction(txn)
      

# 高機能カウンタシャード 
#動的にシャードの数を増やす、名前付きのカウンタをリアルタイムで作成する、memcacheで読み込みを高速化する
class GeneralCounterShardConfig(db.Model):
    #Tracks the number of shards for each named counter.
    name = db.StringProperty(required=True)
    num_shards = db.IntegerProperty(required=True, default=20)


class GeneralCounterShard(db.Model):
    #Shards for each named counter
    name = db.StringProperty(required=True)
    count = db.IntegerProperty(required=True, default=0)


def get_count(name):
    #Retrieve the value for a given sharded counter.

    Parameters:
      name - The name of the counter

    total = memcache.get(name)
    if total is None:
        total = 0
        for counter in GeneralCounterShard.all().filter('name = ', name):
            total += counter.count
        memcache.add(name, str(total), 60)
    return total


def increment(name):
    #Increment the value for a given sharded counter.

    Parameters:
      name - The name of the counter

    config = GeneralCounterShardConfig.get_or_insert(name, name=name)
    def txn():
        index = random.randint(0, config.num_shards - 1)
        shard_name = name + str(index)
        counter = GeneralCounterShard.get_by_key_name(shard_name)
        if counter is None:
            counter = GeneralCounterShard(key_name=shard_name, name=name)
        counter.count += 1
        counter.put()
    db.run_in_transaction(txn)
    memcache.incr(name)


def increase_shards(name, num):
    #Increase the number of shards for a given sharded counter.
    Will never decrease the number of shards.

    Parameters:
      name - The name of the counter
      num - How many shards to use

    
    config = GeneralCounterShardConfig.get_or_insert(name, name=name)
    def txn():
        if config.num_shards < num:
            config.num_shards = num
            config.put()
    db.run_in_transaction(txn)



"""
