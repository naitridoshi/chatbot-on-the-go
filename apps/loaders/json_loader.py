from pathlib import Path

from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from apps.loaders import logger


class JSONDocLoader:

    def __init__(
        self,
        directory: Path,
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
        jq_schema=None,
        content_key=None,
        metadata_func=None,
    ):
        logger.info(
            f"Initializing JSON Loader with directory - {directory} - "
            f"Chunk Size - {chunk_size} - "
            f"Chunk Overlap - {chunk_overlap} - "
            f"Text Splitter - Recursive Character Text Splitter"
        )

        self.directory = directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        self.jq_schema = ".[]" if jq_schema is None else str(jq_schema)
        self.content_key = content_key
        self.metadata_func = metadata_func

    def load_documents(self):
        json_files = list(self.directory.rglob("*.json"))

        logger.debug(
            f"Loading all json files from {self.directory} - "
            f"Found {len(json_files)} to be loaded"
        )

        all_documents = []
        for file_path in json_files:
            loader = JSONLoader(
                str(file_path),
                jq_schema=str(self.jq_schema),
                content_key=self.content_key,
                metadata_func=self.metadata_func,
                text_content=False,
            )

            all_documents.extend(loader.load_and_split(self.text_splitter))

        logger.debug(f"Split loaded documents into {len(all_documents)} chunks")
        return all_documents
