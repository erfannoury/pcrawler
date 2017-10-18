from __future__ import unicode_literals
from hazm import Normalizer
import tweepy
import telegram
import json
import datetime
import time
import pymongo
from mongoHandler import MongoHandler
from config import *
import re
import traceback
from utils import create_temp, remove_dir, make_collage, save_file, telegram_bot, retweetTweet
from os import path

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

maxLikes = None
maxRetweets = None


mongo = MongoHandler(mongo_connString, mongo_db, mongo_collection)
LastTweetToCheck = datetime.datetime.utcnow() - datetime.timedelta(seconds=checkTweetsWithin)
findQuery = {"retweeted_status.created_at": {'$gte': LastTweetToCheck}}
finderCursor = mongo._collection.find(findQuery).limit(4000).sort('retweeted_status.favorite_count', pymongo.DESCENDING)
print(finderCursor.count())
for tweet in finderCursor:
    realStatus = api.get_status(tweet['retweeted_status']['id_str'])
    if realStatus.retweeted:
        continue
    if maxLikes is None:
        maxLikes = tweet.copy()
        break

print("got likes!")

finderCursor = mongo._collection.find(findQuery).limit(4000).sort('retweeted_status.retweet_count', pymongo.DESCENDING)
for tweet in finderCursor:
    realStatus = api.get_status(tweet['retweeted_status']['id_str'])
    if realStatus.retweeted:
        continue
    if maxRetweets is None:
        maxRetweets = tweet.copy()
        break

print("got retweets!")

try:
    if maxLikes['retweeted_status']['id_str'] == maxRetweets['retweeted_status']['id_str']:
        desc = u'این توییت با ' + str(maxLikes['retweeted_status']['favorite_count'])
        desc += u' لایک و ' + str(maxLikes['retweeted_status']['retweet_count']) + u' ریتوییت '
        desc += u'بیشترین لایک و ریتوییت ۱ساعت گذشته را داشته! ✌️🤘🏻\n\n'
        retweetTweet(maxLikes, desc)

    else:
        likesDesc = u'این توییت با ' + str(maxLikes['retweeted_status']['favorite_count'])
        likesDesc += u' لایک '
        likesDesc += u'بیشترین لایک ۱ساعت گذشته را داشته! ✌️🤘🏻\n\n'

        retweetTweet(maxLikes, likesDesc)

        retweetsDesc = u'این توییت با '
        retweetsDesc += str(maxRetweets['retweeted_status']['retweet_count']) + u' ریتوییت '
        retweetsDesc += u'بیشترین ریتوییت ۱ساعت گذشته را داشته! ✌️🤘🏻\n\n'

        retweetTweet(maxRetweets, retweetsDesc)

except Exception as e:
    telegram_bot.sendMessage(chat_id=admin_id, text="الان مشکلی پیش‌اومده!")
    telegram_bot.sendMessage(chat_id=admin_id, text=str(traceback.format_exc()))
    telegram_bot.sendMessage(chat_id=admin_id, text=str(maxLikes['_id']))
    telegram_bot.sendMessage(chat_id=admin_id, text=str(maxRetweets['_id']))


print("likes:")
print(maxLikes['retweeted_status']['favorite_count'])

print("retweets:")
print(maxRetweets['retweeted_status']['retweet_count'])
