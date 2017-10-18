from __future__ import unicode_literals
from hazm import *
import tweepy
import telegram
from nltk.chunk import tree2conlltags
from PIL import Image
from os import path
import tempfile
import shutil
import urllib.request
from config import *

telegram_bot = telegram.Bot(token=telegram_bot_token)
normalizer = Normalizer()

def getTweetText(tweet):
    # gets the main tweet text!
    if 'extended_tweet' in tweet:
        return tweet['extended_tweet']['full_text']
    return tweet['text']

def addFooter(tweet, tp = 'HTML'):
    # adds some footer to tweet generated for telegram Channel
    if tp == 'HTML':
        ret = u'<a href=\"' + 'https://twitter.com/' + tweet['user']['screen_name'] + '/status/' + tweet['id_str'] + '\">لینک به توییت</a>'
        ret += u'\n<a href="https://twitter.com/' + tweet['user']['screen_name'] + '">@' + tweet['user']['screen_name'] + '</a>\n'
        ret += '\n\n📡 @trenditter 📡'
    else:
        ret = 'twitter.com/' + 'statuses/' + tweet['id_str'] + '\n'
        ret += '@trenditter'
    return ret

def getEntities(tweet):
    # gets tweet entities (full entities)!
    if 'extended_tweet' in tweet:
        return getEntities(tweet['extended_tweet'])

    if 'extended_entities' in tweet:
        return tweet['extended_entities']

    if 'entities' in tweet:
        return tweet['entities']

def getTweetType(tweet):
    # gets tweet type (video, photo, text)
    entities = getEntities(tweet)

    if 'media' not in entities:
        return 'text'

    media = entities['media']

    return media[0]['type']



def sendToTelegram(tweet, desc=""):
    # send tweet passed as argument to telegram channel! (first normalize it then send it as whatever it is [video, photo ...])
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

def retweetTweet(tweet_json, desc=""):
    # gets some tweet (in json format from api) and then sends it to Telegram Channel and retweets it!
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    api.retweet(tweet_json['retweeted_status']['id_str'])
    maxLikesTG = sendToTelegram(tweet_json['retweeted_status'], desc)
    telegram_bot.forwardMessage(chat_id=admin_id, from_chat_id="@trenditter", message_id=maxLikesTG.message_id)

def normalize(str):
    if len(str) == 0:
        return str
    if str[-1] is ' ':
        return str[:-1]
    return str

def tree2list(tree):
    str, tag = '', ''
    ret = []
    for item in tree2conlltags(tree):
        if item[2][0] in {'B', 'O'} and tag:
            ret.append((normalize(str), tag))
            tag = ''
            str = ''

        if item[2][0] == 'B':
            tag = item[2].split('-')[1]
            str += ''
        str += item[0] +' '

    if tag:
        ret.append((normalize(str), tag))

    return ret



def make_collage(images, filename, width, init_height):
    """
    Make a collage image with a width equal to `width` from `images` and save to `filename`.
    """
    if not images:
        print('No images for collage found!')
        return False

    margin_size = 2
    # run until a suitable arrangement of images is found
    while True:
        # copy images to images_list
        images_list = images[:]
        coefs_lines = []
        images_line = []
        x = 0
        while images_list:
            # get first image and resize to `init_height`
            img_path = images_list.pop(0)
            img = Image.open(img_path)
            img.thumbnail((width, init_height))
            # when `x` will go beyond the `width`, start the next line
            if x > width:
                coefs_lines.append((float(x) / width, images_line))
                images_line = []
                x = 0
            x += img.size[0] + margin_size
            images_line.append(img_path)
        # finally add the last line with images
        coefs_lines.append((float(x) / width, images_line))

        # compact the lines, by reducing the `init_height`, if any with one or less images
        if len(coefs_lines) <= 1:
            break
        if any(map(lambda c: len(c[1]) <= 1, coefs_lines)):
            # reduce `init_height`
            init_height -= 10
        else:
            break

    # get output height
    out_height = 0
    for coef, imgs_line in coefs_lines:
        if imgs_line:
            out_height += int(init_height / coef) + margin_size
    if not out_height:
        print('Height of collage could not be 0!')
        return False

    collage_image = Image.new('RGB', (width, int(out_height)), (35, 35, 35))
    # put images to the collage
    y = 0
    for coef, imgs_line in coefs_lines:
        if imgs_line:
            x = 0
            for img_path in imgs_line:
                img = Image.open(img_path)
                # if need to enlarge an image - use `resize`, otherwise use `thumbnail`, it's faster
                k = (init_height / coef) / img.size[1]
                if k > 1:
                    img = img.resize((int(img.size[0] * k), int(img.size[1] * k)), Image.ANTIALIAS)
                else:
                    img.thumbnail((int(width / coef), int(init_height / coef)), Image.ANTIALIAS)
                if collage_image:
                    collage_image.paste(img, (int(x), int(y)))
                x += img.size[0] + margin_size
            y += int(init_height / coef) + margin_size
    collage_image.save(filename)
    return True

def create_temp():
    dirpath = tempfile.mkdtemp()
    return dirpath

def remove_dir(dir):
    shutil.rmtree(dir)

def save_file(dir, url):
    name = url.split('/')[-1]
    img_path = path.join(dir, name)
    urllib.request.urlretrieve(url, img_path)
    return img_path
