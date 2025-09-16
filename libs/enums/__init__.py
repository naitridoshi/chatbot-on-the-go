from enum import Enum


class FileType(Enum):
    PDF = "pdf"
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    DOCX = "docx"


class VectorStoreType(Enum):
    CHROMA = "chroma"
    PINECONE = "pinecone"


class LLMType(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"


class Status(Enum):
    CRAWLING = "crawling"
    CRAWLED = "crawled"
    CRAWLING_FAILED = "crawling_failed"
    TRAINING = "training"
    TRAINING_FAILED = "training_failed"
    READY = "ready"
