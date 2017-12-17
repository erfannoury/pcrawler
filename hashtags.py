from __future__ import unicode_literals
from config import *
import pymongo
from mongoHandler import MongoHandler
from utils import getHashtags, createCollectionName
from hazm import *
import datetime
from os import path

d = path.dirname(__file__)
hashtags_blacklist = open(path.join(d, 'hashtags_blacklist.txt')).read().split()

mongo = MongoHandler(mongo_connString, mongo_db, createCollectionName(mongo_collection_format, datetime.datetime.utcnow()))
hashtag_count = {}
hashtag_list = []

lastHashtagCheck = datetime.datetime.utcnow() - datetime.timedelta(seconds=HashtagTimeout)
findQuery = {"timestamp_ms": {'$gte': str(int(lastHashtagCheck.timestamp() * 1000))}}
normalizer = Normalizer()

pipeline_rt = [
    {"$match": findQuery },
    { "$unwind": "$retweeted_status.entities.hashtags" },
    { "$group": { "_id": { "hashtag":"$retweeted_status.entities.hashtags.text"  }, "count":{"$sum":1} } },
    { "$sort": { "count":-1 }},
    { "$limit":  20 },
]

pipeline = [
    {"$match": findQuery },
    { "$unwind": "$entities.hashtags" },
    { "$group": { "_id": { "hashtag":"$entities.hashtags.text"  }, "count":{"$sum":1} } },
    { "$sort": { "count":-1 }},
    { "$limit":  20 },
]

def iterateTweets(pipeline):
    global mongo
    global hashtag_count
    global normalizer

    hashtag_list = list(mongo._collection.aggregate(pipeline))

    for hashtag_it in hashtag_list:
        hashtag_text = normalizer.normalize(hashtag_it['_id']['hashtag'])
        if hashtag_text in hashtags_blacklist:
            continue

        if hashtag_text not in hashtag_count:
            hashtag_count[hashtag_text] = hashtag_it['count']
        else:
            hashtag_count[hashtag_text] += hashtag_it['count']

iterateTweets(pipeline)
iterateTweets(pipeline_rt)
print("first round :D")
if lastHashtagCheck.date() != datetime.datetime.utcnow().date():
    print("i am here bitch!")
    mongo.set_db_and_collection(mongo_db, createCollectionName(mongo_collection_format, lastHashtagCheck))
    iterateTweets(pipeline)
    iterateTweets(pipeline_rt)

for k in sorted(hashtag_count, key=hashtag_count.get, reverse=True)[:10]:
    hashtag_list.append((k, hashtag_count[k]))


text = "هشتگ‌های داغ {} ساعت گذشته:\n".format(HashtagTimeout//tweetAfter)

for it in hashtag_list:
    # print(it)
    text += normalizer.normalize("#{}: {} توییت\n".format(it[0], it[1]))

# print(text)

import telegram
import tweepy

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
api.update_status(text)

telegram_bot = telegram.Bot(token=telegram_bot_token)
ret = telegram_bot.sendMessage(chat_id="@trenditter", text=text)
telegram_bot.forwardMessage(chat_id=admin_id, from_chat_id="@trenditter", message_id=ret.message_id)

# ret = telegram_bot.sendMessage(chat_id=admin_id, text=text)
