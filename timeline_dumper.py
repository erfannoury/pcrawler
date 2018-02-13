import sys
from datetime import datetime
import time

import tweepy
from redis import StrictRedis

import config
from mongoHandler import MongoHandler


auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)


def dump_timeline(uid, mongo):
    """
    Dumps tweets from the timeline of the given user into the given mongo
    collection.

    Parameters
    ----------
    uid: str
        User ID
    mongo: pymongo.collection.Collection
        MongoDB collection for saving the tweets from the user's timeline
    """
    now = datetime.now()
    count = 0
    for page in tweepy.Cursor(api.user_timeline, user_id=uid).pages():
        for status in page:
            try:
                tweet = status._json
                id_str = tweet['id_str']
                del tweet['id_str']
                mongo.insert({
                    '_id': id_str,
                    **tweet})
                count += 1
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print('=' * 20 + ' EXCEPTION IN SAVING A TWEET ' + '=' * 20)
                print(e)
                print('Exception occured at line', exc_tb.tb_lineno)
                print('=' * 60)
                pass

    print('\t{:04} tweets saved. Took {}.'.format(
        count, datetime.now() - now))


if __name__ == '__main__':
    users_mongo = MongoHandler(
        config.mongo_connString, config.mongo_db,
        config.mongo_users_collection)
    timelines_mongo = MongoHandler(
        config.mongo_connString, config.mongo_db,
        config.mongo_timelines_collection)

    users_set = set(users_mongo._collection.distinct(key='_id'))
    tmln_users_set = set(timelines_mongo._collection.distinct(
        key='user.id_str'))

    unique_users = users_set - tmln_users_set

    total_count = len(unique_users)
    for i, uid in enumerate(unique_users):
        if i % 1000 == 0:
            print(datetime.now())
        try:
            # if not api.get_user(user_id=uid).protected:
            print(f'{i:06}/{total_count:06}', end='')
            dump_timeline(uid, timelines_mongo)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print('=' * 20 + f' EXCEPTION IN USER {uid} ' + '=' * 20)
            print(e)
            print('Exception occured at line', exc_tb.tb_lineno)
            print('=' * 60)
