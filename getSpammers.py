from config import *
import pymongo
from mongoHandler import MongoHandler
from bson.son import SON
from utils import createCollectionName
import datetime

mongo = MongoHandler(mongo_connString, mongo_db, createCollectionName(mongo_collection_format, datetime.datetime.utcnow()))

# pipeline = [
#     {"$group" : { "_id": "$user.screen_name", "count": { "$sum": 1 } } },
#     {"$match": {"_id" :{ "$ne" : "" } , "count" : {"$gt": 1} } },
#     {"$sort": {"count" : -1} }
# ]
#
# userslist = list(mongo._collection.aggregate(pipeline))
# spammers = set()
#
# for it in userslist:
#     if it['count'] > 120:
#         print(it['_id'], ", ", it['count'])
#         spammers.add(it['_id'])
#     else:
#         break

# for spammer in spammers:

s = '#فرزند_امام_زمان *'

import re
regx = re.compile(s, re.IGNORECASE)

ret = mongo._collection.delete_many({"text": regx})
print("deleted {} tweets from {}".format(ret.deleted_count, s))
