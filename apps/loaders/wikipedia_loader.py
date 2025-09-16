from langchain_community.document_loaders import WikipediaLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from apps.loaders import logger


class WikipediaPageLoader:
    def __init__(
        self,
        query: str,
        lang: str = "en",
        load_max_docs=2,
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
    ):
        logger.info(
            f"Initializing Wikipedia Loader with query - {query} - "
            f"Language - {lang} - "
            f"Chunk Size - {chunk_size} - "
            f"Chunk Overlap - {chunk_overlap} - "
            f"Text Splitter - Recursive Character Text Splitter",
            extra={"self": self},
        )

        self.query = query
        self.lang = lang
        self.load_max_docs = load_max_docs
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def load_documents(self):
        logger.debug(f"Loading Wikipedia article for query: {self.query}")

        loader = WikipediaLoader(
            query=self.query, lang=self.lang, load_max_docs=self.load_max_docs
        )
        documents = loader.load_and_split(self.text_splitter)

        logger.debug(f"Split loaded documents into {len(documents)} chunks")
        return documents
