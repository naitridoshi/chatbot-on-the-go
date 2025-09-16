from pydantic import BaseModel

from libs.enums import LLMType


class QueryInputModel(BaseModel):
    name: str
    user_query: str
    prompt: str | None = None
    use_context: bool | None = True
    llm: LLMType
