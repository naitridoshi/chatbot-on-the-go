from pydantic import BaseModel, HttpUrl


class CrawlerInputModel(BaseModel):
    name: str
    website: HttpUrl
