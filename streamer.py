import tweepy
import json
import datetime
import time
from mongoHandler import MongoHandler
from config import *
from os import path
from utils import getHashtags, createCollectionName

d = path.dirname(__file__)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
last_updated = datetime.datetime.utcnow()
collection_name = createCollectionName(mongo_collection_format, last_updated)

# This is the listener, resposible for receiving data
class StdOutListener(tweepy.StreamListener):

    _mongo = MongoHandler(mongo_connString, mongo_db, collection_name)
    _blacklist = open(path.join(d, 'users_blacklist.txt')).read().split()
    _hashtags_blacklist = open(path.join(d, 'hashtags_blacklist.txt')).read().split()

    def on_data(self, data):
        tweet = json.loads(data)
        global last_updated
        global collection_name

        if last_updated.date() != datetime.datetime.utcnow().date():
            last_updated = datetime.datetime.utcnow()
            collection_name = createCollectionName(mongo_collection_format, last_updated)
            self._mongo.set_collection(collection_name)

        if 'retweeted_status' in tweet:
            tcreated = datetime.datetime.strptime(tweet['retweeted_status']['created_at'], '%a %b %d %H:%M:%S %z %Y').replace(tzinfo=None)
            tweet['retweeted_status']['created_at'] = tcreated
            tweet_text = tweet['retweeted_status']['text']
            sender = tweet['retweeted_status']['user']['screen_name']
        else:
            tcreated = datetime.datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y').replace(tzinfo=None)
            tweet['created_at'] = tcreated
            tweet_text = tweet['text']
            sender = tweet['user']['screen_name']

        hashtags_entities = getHashtags(tweet)
        hashtags_list = [hashtag['text'] in self._hashtags_blacklist for hashtag in hashtags_entities]

        if u'ة' not in tweet_text and u'أ' not in tweet_text and sender not in self._blacklist and True not in hashtags_list:
            self._mongo.insert(tweet)
        return True

    def on_error(self, status):
        print(status)


if __name__ == '__main__':
    listener = StdOutListener()

    print("streaming all new tweets for persian language!")

    # There are different kinds of streams: public stream, user stream,
    #    multi-user streams
    # In this example follow #programming tag
    # For more details refer to https://dev.twitter.com/docs/streaming-apis
    stream = tweepy.Stream(auth, listener)
    stream.filter(track=[u'با', u'هر', u'از', u'و', u'من',
                  u'تا', u'به', u'را', u'رو', u'که'],
                  languages=['fa'])
