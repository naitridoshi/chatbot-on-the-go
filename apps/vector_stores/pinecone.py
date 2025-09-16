from datetime import datetime
from uuid import uuid4

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from apps.vector_stores import logger
from libs.config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME, GEMINI_API_KEY, GOOGLE_EMBEDDING_MODEL,
)


class PineconeManager:

    def __init__(
        self,
        api_key: str = PINECONE_API_KEY,
        index_name: str | None = None,
        dimension: int = 768,  # Set to 768 for GoogleGenerativeAIEmbeddings
        embeddings=None,
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1",
    ):
        self.api_key = api_key
        self.index_name = index_name or PINECONE_INDEX_NAME
        self.dimension = dimension
        self.metric = metric
        self.cloud = cloud
        self.region = region
        self.pinecone_client = Pinecone(api_key=self.api_key)
        self.embeddings = embeddings or GoogleGenerativeAIEmbeddings(
            model=GOOGLE_EMBEDDING_MODEL,
            google_api_key=GEMINI_API_KEY,
            task_type="RETRIEVAL_DOCUMENT"
        )
        self.vector_store = None

    def _delete_first_index(self):
        try:
            indexes = self.pinecone_client.list_indexes().names()
            if not indexes:
                logger.info("No indexes to delete.")
                return

            index_to_delete = indexes[0]
            logger.warning(
                f"Max indexes reached. Deleting first available index to make space: {index_to_delete}")
            self.pinecone_client.delete_index(index_to_delete)
            logger.info(f"Successfully deleted index: {index_to_delete}")

        except Exception as e:
            logger.error(f"Error while trying to delete an index: {e}")
            raise

    def get_vector_store(self):
        logger.info(
            f"Creating Pinecone Vector Store Object - "
            f"Index Name - {self.index_name} - "
            f"Dimensions - {self.dimension}"
        )

        existing_indexes = self.pinecone_client.list_indexes().names()
        if self.index_name in existing_indexes:
            index_description = self.pinecone_client.describe_index(
                self.index_name)
            if index_description.dimension != self.dimension:
                logger.warning(
                    f"Index '{self.index_name}' exists with dimension {index_description.dimension}, "
                    f"but required dimension is {self.dimension}. Deleting and recreating index."
                )
                self.pinecone_client.delete_index(self.index_name)
                self._create_index_with_retry()
            else:
                logger.info(
                    f"Index '{self.index_name}' already exists with correct dimension.")
        else:
            self._create_index_with_retry()

        vector_store = PineconeVectorStore(
            index_name=self.index_name,
            pinecone_api_key=self.api_key,
            embedding=self.embeddings,
        )

        self.vector_store = vector_store
        return vector_store

    def _create_index_with_retry(self):
        logger.debug(f"Creating new Index: {self.index_name}")
        try:
            self.pinecone_client.create_index(
                self.index_name,
                dimension=self.dimension,
                spec=ServerlessSpec(cloud=self.cloud, region=self.region),
            )
        except Exception as e:
            if "403" in str(e) and "max serverless indexes" in str(e).lower():
                logger.warning(
                    f"Index creation failed (Max indexes reached). Attempting to delete an index and retry.")
                self._delete_first_index()
                logger.info(f"Retrying index creation for: {self.index_name}")
                self.pinecone_client.create_index(
                    self.index_name,
                    dimension=self.dimension,
                    spec=ServerlessSpec(cloud=self.cloud, region=self.region),
                )
            else:
                raise

    def store_documents(self, loaded_documents: list):
        logger.info(
            f"Storing - {len(loaded_documents)} documents in the pinecone vector store"
        )

        if self.vector_store is None:
            logger.error("Pinecone Vector Store Object is not created.")
            raise Exception("Pinecone Vector Store Object Not Formed.")

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
            f"All Documents successfully stored in the pinecone vector store with index - {self.index_name}"
        )