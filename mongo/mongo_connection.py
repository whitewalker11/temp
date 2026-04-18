from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "your_database"


def get_database():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return client, db