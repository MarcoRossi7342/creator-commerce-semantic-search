from typing import Literal

from pydantic import BaseModel, Field


ContentKind = Literal["digital_asset_delivery", "subscriber_update"]


class CreatorContent(BaseModel):
    content_id: str = Field(min_length=1)
    creator_id: str = Field(min_length=1)
    kind: ContentKind
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)


class IndexRequest(BaseModel):
    collection: str = Field(min_length=1)
    items: list[CreatorContent] = Field(min_length=1)


class SearchRequest(BaseModel):
    collection: str = Field(min_length=1)
    query: str = Field(min_length=1)
    creator_id: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchHit(BaseModel):
    content_id: str
    score: float
    kind: ContentKind
    title: str
    next_action: Literal["open_download", "read_update"]


class SearchResponse(BaseModel):
    hits: list[SearchHit]
