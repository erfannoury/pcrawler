def getTweetText(tweet):
    # gets the main tweet text!
    if 'extended_tweet' in tweet:
        return tweet['extended_tweet']['full_text']
    return tweet['text']


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


def getPhotos(tweet):
    # returns list of photos in tweet
    entities = tweet['entities']
    photos_list = [media for media in entities['media']]
    return photos_list


def getURLs(tweet):
    if 'extended_tweet' in tweet:
        return getURLs(tweet['extended_tweet'])

    entities_urls = tweet['entities']['urls']
    return entities_urls


def getHashtags(tweet):
    if 'retweeted_status' in tweet:
        return getHashtags(tweet['retweeted_status'])

    if 'extended_tweet' in tweet:
        return getHashtags(tweet['extended_tweet'])

    hashtagsEntities = tweet['entities']['hashtags']
    return hashtagsEntities
