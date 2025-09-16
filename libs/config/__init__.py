import os
from os import path

from dotenv import dotenv_values

env_path = ".env"

if not path.exists(env_path):
    raise Exception(".env request_file not found")

config = dotenv_values(env_path)

CURRENT_WORKING_DIR = os.getcwd()

PINECONE_API_KEY = config.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = config.get("PINECONE_INDEX_NAME")
OPENAI_API_KEY = config.get("OPENAI_API_KEY")
CHROMA_COLLECTION_NAME = config.get("CHROMA_COLLECTION_NAME")
CHROMA_PERSIST_DIRECTORY = os.path.join(
    CURRENT_WORKING_DIR, config.get("CHROMA_PERSIST_DIRECTORY")
)
OPENAI_EMBEDDING_MODEL = config.get("OPENAI_EMBEDDING_MODEL")
OPENAI_MODEL = config.get("OPENAI_MODEL")
GEMINI_MODEL = config.get("GEMINI_MODEL")
GEMINI_API_KEY = config.get("GEMINI_API_KEY")
MONGO_URI = config.get("MONGO_URI")
DATABASE_NAME = config.get("DATABASE_NAME")
HOST = config.get("HOST")
PORT = int(config.get("PORT"))
ENVIRONMENT = config.get("ENVIRONMENT")
ANTHROPIC_MODEL = config.get("ANTHROPIC_MODEL")
ANTHROPIC_API_KEY = config.get("ANTHROPIC_API_KEY")

GOOGLE_EMBEDDING_MODEL =config.get("GOOGLE_EMBEDDING_MODEL")