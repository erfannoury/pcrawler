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
from utils import create_temp, remove_dir, make_collage, save_file
from os import path

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
telegram_bot = telegram.Bot(token=telegram_bot_token)
normalizer = Normalizer()

def getTweetText(tweet):
    if 'extended_tweet' in tweet:
        return tweet['extended_tweet']['full_text']
    return tweet['text']

def addFooter(tweet, tp = 'HTML'):
    if tp == 'HTML':
        ret = u'<a href=\"' + 'https://twitter.com/' + tweet['user']['screen_name'] + '/status/' + tweet['id_str'] + '\">لینک به توییت</a>'
        ret += u'\n<a href="https://twitter.com/' + tweet['user']['screen_name'] + '">@' + tweet['user']['screen_name'] + '</a>\n'
        ret += '\n\n📡 @trenditter 📡'
    else:
        ret = 'twitter.com/' + 'statuses/' + tweet['id_str'] + '\n'
        ret += '@trenditter'
    return ret

def getEntities(tweet):
    if 'extended_tweet' in tweet:
        return getEntities(tweet['extended_tweet'])

    if 'extended_entities' in tweet:
        return tweet['extended_entities']

    if 'entities' in tweet:
        return tweet['entities']

def getTweetType(tweet):
    entities = getEntities(tweet)

    if 'media' not in entities:
        return 'text'

    media = entities['media']

    return media[0]['type']



def sendToTelegram(tweet, desc=""):
    tweet_text = getTweetText(tweet)
    tweet_text = tweet_text
    desc = normalizer.normalize(desc)

    text = ''
    pre = ' '.join(re.sub("(@[A-Za-z0-9_]+)|(?:\@|https?\://)\S+", " ", tweet_text).split())
    pre = normalizer.normalize(pre)

    text += tweet['user']['name'] + u":\n"
    text += pre + '\n'

    Type = getTweetType(tweet)

    if Type == 'text':
        text += '\n' + desc + '\n\n'
        text += addFooter(tweet, 'HTML')
        ret = telegram_bot.sendMessage(chat_id="@trenditter", text=text, parse_mode=telegram.ParseMode.HTML)

    elif Type == 'photo':

        text += addFooter(tweet, 'PLAIN')

        entities = getEntities(tweet)
        tempdir = create_temp()

        images = [save_file(tempdir, media['media_url']) for media in entities['media']]

        output_name = path.join(tempdir, "collage.png")

        if len(images) > 1:
            width = 1600
            init_height = 800

            make_collage(images, output_name, width, init_height)
        else:
            output_name = images[0]
            
        ret = telegram_bot.send_photo(chat_id="@trenditter", photo=open(output_name, 'rb'), caption=text)

        remove_dir(tempdir)

    else:

        text += addFooter(tweet, 'PLAIN')
        entities = getEntities(tweet)
        tempdir = create_temp()

        videos = entities['media'][0]['video_info']['variants']

        for video in videos:
            if video['content_type'] == 'video/mp4':
                video_path = video['url']

        ret = telegram_bot.send_video(chat_id="@trenditter", video=video_path, caption=text)

    return ret



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

        api.retweet(maxLikes['retweeted_status']['id_str'])
        maxLikesTG = sendToTelegram(maxLikes['retweeted_status'], desc)
        telegram_bot.forwardMessage(chat_id=admin_id, from_chat_id="@trenditter", message_id=maxLikesTG.message_id)

    else:
        likesDesc = u'این توییت با ' + str(maxLikes['retweeted_status']['favorite_count'])
        likesDesc += u' لایک '
        likesDesc += u'بیشترین لایک ۱ساعت گذشته را داشته! ✌️🤘🏻\n\n'

        api.retweet(maxLikes['retweeted_status']['id_str'])

        maxLikesTG = sendToTelegram(maxLikes['retweeted_status'], likesDesc)

        print('maxLikesText tweeted!')
        telegram_bot.forwardMessage(chat_id=admin_id, from_chat_id="@trenditter", message_id=maxLikesTG.message_id)

        retweetsDesc = u'این توییت با '
        retweetsDesc += str(maxRetweets['retweeted_status']['retweet_count']) + u' ریتوییت '
        retweetsDesc += u'بیشترین ریتوییت ۱ساعت گذشته را داشته! ✌️🤘🏻\n\n'

        api.retweet(maxRetweets['retweeted_status']['id_str'])
        maxRtTG = sendToTelegram(maxRetweets['retweeted_status'], retweetsDesc)

        print('maxRetweetsText tweeted!')
        telegram_bot.forwardMessage(chat_id=admin_id, from_chat_id="@trenditter", message_id=maxRtTG.message_id)

except Exception as e:
    telegram_bot.sendMessage(chat_id=admin_id, text="الان مشکلی پیش‌اومده!")
    telegram_bot.sendMessage(chat_id=admin_id, text=str(traceback.format_exc()))
    telegram_bot.sendMessage(chat_id=admin_id, text=str(maxLikes['_id']))
    telegram_bot.sendMessage(chat_id=admin_id, text=str(maxRetweets['_id']))


print("likes:")
print(maxLikes['retweeted_status']['favorite_count'])

print("retweets:")
print(maxRetweets['retweeted_status']['retweet_count'])
