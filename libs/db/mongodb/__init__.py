from pymongo import MongoClient
from pymongo.errors import PyMongoError

from libs.config import DATABASE_NAME, MONGO_URI
from libs.logger import get_logger

logger, listener = get_logger("mongodb")
listener.start()


def connect_db():
    try:
        client = MongoClient(MONGO_URI)
        return client[DATABASE_NAME]
    except PyMongoError as error:
        raise Exception(
            f'Failed to connect to database: "{DATABASE_NAME}",'
            f"ERROR: {str(error)}"
        )


db = connect_db()
sessions_collection = db["sessions"]
conversations_collection = db["conversations"]
