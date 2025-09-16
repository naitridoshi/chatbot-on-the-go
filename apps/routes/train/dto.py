import re
from pydantic import BaseModel, model_validator, field_validator

from libs.enums import FileType, VectorStoreType


class TrainInputModel(BaseModel):
    name: str
    file: bool = False
    web: bool = False
    file_type: FileType | None = None
    directory_name: str | None = None
    vector_store: VectorStoreType
    yt_links: list | None = None
    chroma_collection_name: str | None = None
    pinecone_index_name: str | None = None
    wikipedia_query: str | None = None

    @field_validator("pinecone_index_name", "chroma_collection_name")
    def sanitize_name(cls, v: str) -> str:
        if not v:
            return v
        # Convert to lowercase
        v = v.lower()
        # Replace spaces and underscores with hyphens
        v = re.sub(r'[\s_]+', '-', v)
        # Keep only lowercase letters, numbers, and hyphens
        v = re.sub(r'[^a-z0-9-]', '', v)
        # Ensure it doesn't start or end with a hyphen
        v = v.strip('-')
        if not v:
            raise ValueError("Name must contain at least one alphanumeric character.")
        return v

    @model_validator(mode="after")
    def validate_input_combination(self):

        if self.file and self.file_type is None:
            raise ValueError("file_type must be provided when file is True")

        if self.web and self.yt_links is None and self.wikipedia_query is None:
            raise ValueError(
                "Either yt_links or wikipedia_query must be provided when web is True"
            )

        if (
            self.vector_store == VectorStoreType.CHROMA
            and self.chroma_collection_name is None
        ):
            raise ValueError(
                "chroma_collection_name must be provided when vector_store is chroma"
            )

        if (
            self.vector_store == VectorStoreType.PINECONE
            and self.pinecone_index_name is None
        ):
            raise ValueError(
                "pinecone_index_name must be provided when vector_store is pinecone"
            )

        return self