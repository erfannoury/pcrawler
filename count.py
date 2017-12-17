from config import *
import pymongo
from mongoHandler import MongoHandler

mongo = MongoHandler(mongo_connString, mongo_db)
collections = mongo._db.collection_names(include_system_collections=False)
tweets = 0
users_list = set()

for collection in collections:
    mongo.set_collection(collection)
    curr_tweets = mongo._collection.find().count()
    if curr_tweets <= 5e6:
        curr_list = mongo._collection.distinct("user.id_str")
        for it in curr_list:
            users_list.add(it)
        curr_users = len(curr_list)
    else:
        curr_users = 1e9
    print("{}: \t{:,}\t{:,}".format(collection, curr_tweets, curr_users))
    tweets += curr_tweets

print("+-------\ntotal: {:,}".format(tweets))
print("users: {:,}".format(len(users_list)))
