import os
from pymongo import MongoClient, ASCENDING

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB = os.getenv("MONGO_DB", "products_db")


def get_mongo_client():
    return MongoClient(host=MONGO_HOST, port=MONGO_PORT)


def get_products_collection():
    client = get_mongo_client()
    db = client[MONGO_DB]
    return db["products"]


def init_mongo():
    products_col = get_products_collection()
    products_col.create_index([("name", ASCENDING)], unique=True)
