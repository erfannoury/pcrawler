import sys
import datetime
import json

import tweepy
from redis import StrictRedis

import config
from mongoHandler import MongoHandler
from utils import getHashtags

auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
api = tweepy.API(auth)
tweet_counter = 0


class StdOutListener(tweepy.StreamListener):
    """
    This is the listener, resposible for receiving data
    """
    tweets_mongo = MongoHandler(
        config.mongo_connString, config.mongo_db,
        config.mongo_uniquetweets_collection)
    retweets_mongo = MongoHandler(
        config.mongo_connString, config.mongo_db,
        config.mongo_retweets_collection)
    users_mongo = MongoHandler(
        config.mongo_connString, config.mongo_db,
        config.mongo_users_collection)

    tweets_redis = StrictRedis(
        host='localhost', port=config.redis_port, db=config.redis_tweets_db)
    users_redis = StrictRedis(
        host='localhost', port=config.redis_port, db=config.redis_users_db)
    time_redis = StrictRedis(
        host='localhost', port=config.redis_port, db=config.redis_time_db)

    _blacklist = open('users_blacklist.txt').read().split()
    _hashtags_blacklist = open(
        'hashtags_blacklist.txt', encoding='utf-8').read().split()

    def on_data(self, data):
        """
        Called when raw data is received from connection.
        Return False to stop stream and close connection.
        """
        global tweet_counter
        tweet_counter += 1
        if not tweet_counter % 1000:
            print('{} ---- {} tweets streamed so far.'.format(
                datetime.datetime.now(), tweet_counter))

        tweet = json.loads(data)
        user = tweet['user']

        tcreated = datetime.datetime.strptime(
            tweet['created_at'],
            '%a %b %d %H:%M:%S %z %Y'
        ).replace(tzinfo=None)
        self.time_redis.set(tweet['id_str'], tcreated)

        uid = user['id_str']
        del user['id_str']
        if not self.users_redis.exists(uid):
            self.users_mongo.insert({
                '_id': uid,
                **user
            })
            self.users_redis.set(uid, 1)
        else:
            self.users_redis.incr(uid)

        initial_retweet_count = 0
        if 'retweeted_status' in tweet:
            tcreated = datetime.datetime.strptime(
                tweet['retweeted_status']['created_at'],
                '%a %b %d %H:%M:%S %z %Y'
            ).replace(tzinfo=None)
            tweet['retweeted_status']['created_at'] = tcreated
            try:
                self.retweets_mongo.insert({
                    '_id': tweet['id_str'],
                    'user_id': uid,
                    'retweeted_id': tweet['retweeted_status']['id_str'],
                    'retweeted_user_id': tweet[
                        'retweeted_status']['user']['id_str']
                })
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print('=' * 20 + ' EXCEPTION IN SAVING RETWEET ' + '=' * 20)
                print(e)
                print('Exception occured at line', exc_tb.tb_lineno)
                print('=' * 69)
                pass

            if not self.tweets_redis.exists(
                tweet['retweeted_status']['id_str']):
                initial_retweet_count = 1
            else:
                self.tweets_redis.incr(tweet['retweeted_status']['id_str'])

            tweet['retweeted_status']['created_at'] = tcreated
            tweet = tweet['retweeted_status']
        else:
            tcreated = datetime.datetime.strptime(
                tweet['created_at'],
                '%a %b %d %H:%M:%S %z %Y'
            ).replace(tzinfo=None)
            tweet['created_at'] = tcreated

        hashtags_list = [
            hashtag['text'] in self._hashtags_blacklist for hashtag in
            getHashtags(tweet)]

        if u'ة' not in tweet['text'] and u'أ' not in tweet['text'] and \
        user['screen_name'] not in self._blacklist and not any(hashtags_list):
            if not self.tweets_redis.exists(tweet['id_str']):
                self.tweets_redis.set(tweet['id_str'], initial_retweet_count)
                id_str = tweet['id_str']
                del tweet['id_str']

                self.tweets_mongo.insert({
                    '_id': id_str,
                    **tweet
                })

        return True

    def on_error(self, status):
        print('=' * 20 + " Error occured in Twitter streaming " + '=' * 20)
        print(status)
        print('=' * 20 + " Error occured in Twitter streaming " + '=' * 20)
        return False


if __name__ == '__main__':

    while True:
        try:
            listener = StdOutListener()
            print("(re)starting to stream new Persian tweets at",
                  datetime.datetime.now())
            stream = tweepy.Stream(auth, listener)
            stream.filter(
                track=[u'با', u'هر', u'از', u'و', u'من',
                       u'تا', u'به', u'را', u'رو', u'که'],
                languages=['fa'])

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print('=' * 20 + ' EXCEPTION IN TWITTER STREAMING ' + '=' * 20)
            print(e)
            print('Exception occured at line', exc_tb.tb_lineno)
            print('=' * 72)
            pass
