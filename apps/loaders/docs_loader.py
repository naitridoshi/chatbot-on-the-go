from pathlib import Path

from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from apps.loaders import logger


class DocsLoader:

    def __init__(
        self, directory: Path, chunk_size: int = 1024, chunk_overlap: int = 200
    ):
        logger.info(
            f"Initializing Docs Loader with directory - {directory} - "
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

    def load_documents(self):
        docx_files = list(self.directory.rglob("*.docx"))

        logger.debug(
            f"Loading all docx files from {self.directory} - "
            f"Found {len(docx_files)} to be loaded"
        )

        all_documents = []
        for file_path in docx_files:
            loader = UnstructuredWordDocumentLoader(str(file_path))
            all_documents.extend(loader.load_and_split(self.text_splitter))

        logger.debug(f"Split loaded documents into {len(all_documents)} chunks")
        return all_documents
