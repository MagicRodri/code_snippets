import logging
from typing import Iterable, List, Set

import config
import pymongo

if config.DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
# Connect to MongoDB
mongo_user = config.MG_USER
mongo_pass = config.MG_PASSWORD
mongo_cluster = config.MG_CLUSTER

try:
    logging.info("Connecting to MongoDB...")

    client = pymongo.MongoClient(f"mongodb+srv://{mongo_user}:{mongo_pass}@{mongo_cluster}")

    metrics = client.metrics
    ohlcv_db = metrics.ohlcv_db
    posts_db = metrics.posts_db
except Exception as e:
    logging.error("Error connecting to MongoDB:", e)


def get_top_pairs(max_num:int=100) -> List:
    """
        Function to return at most the top max_num distinct pairs by compound volume from ohlcv db
    """
    try:
        logging.info("Getting top pairs by volume...")
        ohlcv_documents = ohlcv_db.find({},{'_id':False}).sort('volume', pymongo.DESCENDING)
    except Exception as e:
        logging.error("Error getting top pairs:", e)
        return list()

    top_100_pairs_by_volume_set = set()
    top_100_pairs_by_volume = list()
    for item in ohlcv_documents:

        pair = f"{item['pair_symbol'].upper()}-{item['pair_base'].upper()}"
        if pair not in top_100_pairs_by_volume_set:
            top_100_pairs_by_volume_set.add(pair)
            top_100_pairs_by_volume.append(pair)
            
        if len(top_100_pairs_by_volume) == max_num:
            break
    return top_100_pairs_by_volume


def get_latest_posted_pairs(top_pairs:List,max_num:int=5) -> Set:
    """
        Function to return at most the top max_num distinct pairs by latest post time from posts db
    """
    try:
        logging.info("Getting oldest posted pairs...")
        posted_pairs_among_top = posts_db.find({'pair' : {'$in':top_pairs}}).sort('time', pymongo.DESCENDING).distinct('pair')
    except Exception as e:
        logging.error("Error getting oldest posted pairs:", e)
        return set()

    posted_pairs_set_among_top = set()

    # At most top max_num distinct latest posted pairs among top pairs
    for pair in posted_pairs_among_top:
        if pair not in posted_pairs_set_among_top:
            posted_pairs_set_among_top.add(pair)
        if len(posted_pairs_set_among_top) == max_num:
            break
    return posted_pairs_set_among_top

def get_latest_posted_pair() -> str:
    """
        Function to return the latest posted pair
    """
    try:
        logging.info("Getting latest posted pair...")
        document = posts_db.find({}).sort('time', pymongo.DESCENDING).limit(1)
    except Exception as e:
        logging.error("Error getting latest posted pair:", e)
        return str()
    return document[0].get('pair')

def get_pair_to_post(top_pairs:List,oldest_posted_pairs:Iterable = None) -> str:
    """
        Function to return the pair to post
    """
    try:
        logging.info("Getting pair to post...")
        if (oldest_posted_pairs is None) or len(oldest_posted_pairs) == 0:
            # the first pair by volume
            return top_pairs[0]

        last_posted = get_latest_posted_pair()
        for pair in top_pairs:
            if pair in oldest_posted_pairs and not pair == last_posted:
                # Choose the first pair by volume among those oldest posted pairs
                return pair
        else:
            # Or the first pair by volume
            return top_pairs[0]
    except Exception as e:
        logging.error("Error getting pair to post:", e)
        return str()
if __name__ == "__main__":

    top = ['A','B','C']
    assert('A' == get_pair_to_post(top,oldest_posted_pairs={}))
    assert('B' == get_pair_to_post(top,oldest_posted_pairs={'B'}))
    print(ohlcv_db.count_documents({}))
    print(posts_db.count_documents({}))