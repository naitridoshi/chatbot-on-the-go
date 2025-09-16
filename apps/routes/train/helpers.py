import os.path
import shutil
from pathlib import Path

from apps.loaders.csv_loader import CSVLoader
from apps.loaders.docs_loader import DocsLoader
from apps.loaders.json_loader import JSONDocLoader
from apps.loaders.pdf_loader import PDFLoader
from apps.loaders.txt_loader import TxtLoader
from apps.loaders.wikipedia_loader import WikipediaPageLoader
from apps.loaders.youtube_transcripts_loader import YoutubeUrlLoader
from apps.routes.train import logger
from apps.routes.train.dto import TrainInputModel
from apps.vector_stores.chroma_db import ChromaManager
from apps.vector_stores.pinecone import PineconeManager
from libs.enums import FileType, VectorStoreType


def load_documents(train_data=TrainInputModel, directory: Path | None = None):
    logger.debug(
        f"Loading Documents of file type - {train_data.file_type.name if train_data.file_type else None} - "
        f"From Directory - {str(directory)} - "
        f"Youtube Links Provided - {train_data.yt_links is not None } - "
        f"Wikipedia Query Provided - {train_data.wikipedia_query is not None} "
    )

    all_documents = []
    loader_mapping = {
        FileType.PDF: PDFLoader,
        FileType.DOCX: DocsLoader,
        FileType.CSV: CSVLoader,
        FileType.JSON: JSONDocLoader,
        FileType.TXT: TxtLoader,
    }

    if train_data.file:
        loader_class = loader_mapping.get(train_data.file_type)
        logger.debug(f"Received Loader Class - {loader_class.__name__} ")
        loader = loader_class(directory=directory)
        all_documents.extend(loader.load_documents())

    if train_data.web:
        if train_data.yt_links:
            loader = YoutubeUrlLoader()
            all_documents.extend(
                loader.load_documents(youtube_links=train_data.yt_links)
            )
        if train_data.wikipedia_query:
            loader = WikipediaPageLoader(query=train_data.wikipedia_query)
            all_documents.extend(loader.load_documents())

    if directory and directory.exists():
        logger.debug(f"Cleaning up directory - {str(directory)}")
        shutil.rmtree(directory)

    return all_documents


def store_documents(documents: list, train_data: TrainInputModel):
    if train_data.vector_store == VectorStoreType.CHROMA:
        vector_store_object = ChromaManager(
            collection_name=train_data.chroma_collection_name
        )
    else:
        vector_store_object = PineconeManager(
            index_name=train_data.pinecone_index_name
        )

    vector_store_object.get_vector_store()
    vector_store_object.store_documents(loaded_documents=documents)