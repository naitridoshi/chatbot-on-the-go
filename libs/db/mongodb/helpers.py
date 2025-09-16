from datetime import datetime, timezone

from libs.db.mongodb import (
    conversations_collection,
    logger,
    sessions_collection,
)


def store_session(document_to_insert: dict):
    logger.debug(
        f"Storing Session - {document_to_insert.get('name')} - {document_to_insert.get('vector_store')}"
    )
    document_to_insert["createdAt"] = datetime.now(timezone.utc)
    document_to_insert["updatedAt"] = datetime.now(timezone.utc)
    sessions_collection.insert_one(document_to_insert)


def get_sessions(name: str):
    logger.debug(f"Getting Session Details for - {name}")
    session_data = sessions_collection.find_one({"name": name})
    return session_data


def update_session(name: str, document_to_update: dict):
    logger.debug(f"Updating Session - {name}")
    document_to_update["updatedAt"] = datetime.now(timezone.utc)
    sessions_collection.update_one(
        {"name": name},
        {"$set": document_to_update, "$setOnInsert": {"createdAt": datetime.now(timezone.utc)}},
        upsert=True
    )


def store_conversations(document_to_insert: dict):
    logger.debug(
        f"Storing conversations - {document_to_insert.get('name')} - query - {document_to_insert.get('user_query')}"
    )
    document_to_insert["createdAt"] = datetime.now(timezone.utc)
    document_to_insert["updatedAt"] = datetime.now(timezone.utc)
    conversations_collection.insert_one(document_to_insert)
