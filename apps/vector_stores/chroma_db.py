from uuid import uuid4

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from apps.vector_stores import logger
from libs.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIRECTORY,
    GEMINI_API_KEY, GOOGLE_EMBEDDING_MODEL,
)


class ChromaManager:

    def __init__(
        self,
        collection_name: str | None = None,
        embeddings=None,
        persist_directory: str = CHROMA_PERSIST_DIRECTORY,
    ):
        self.collection_name = collection_name or CHROMA_COLLECTION_NAME
        self.embeddings = embeddings or GoogleGenerativeAIEmbeddings(
            model=GOOGLE_EMBEDDING_MODEL,
            google_api_key=GEMINI_API_KEY,
            task_type="RETRIEVAL_DOCUMENT"
        )
        self.persist_directory = persist_directory
        self.vector_store = None

    def get_vector_store(self):
        logger.info(
            f"Creating Chroma Vector Store Object - "
            f"Collection Name - {self.collection_name} - "
            f"Persist Directory - {self.persist_directory}"
        )

        vector_store = Chroma(
            collection_name=str(self.collection_name),
            embedding_function=self.embeddings,
            client_settings=chromadb.config.Settings(
                anonymized_telemetry=False
            ),
            persist_directory=str(self.persist_directory)
            + str(f"/{self.collection_name}"),
        )

        self.vector_store = vector_store
        return vector_store

    def store_documents(self, loaded_documents: list):
        logger.info(
            f"Storing - {len(loaded_documents)} documents in the chroma vector store"
        )

        if self.vector_store is None:
            logger.error("Chroma Vector Store Object is not created.")
            raise Exception("Chroma Vector Store Object Not Formed.")

        documents = [
            Document(
                page_content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in loaded_documents
        ]

        uuids = [str(uuid4()) for _ in range(len(documents))]

        self.vector_store.add_documents(documents=documents, uuids=uuids)

        logger.info(
            f"All Documents successfully stored in the chroma vector store with collection name - {self.collection_name}"
        )
