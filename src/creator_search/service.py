import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException

from creator_search.content_search import ContentSearch
from creator_search.infrai_client import InfraiClient, InfraiError
from creator_search.models import IndexRequest, SearchRequest, SearchResponse


def build_app() -> FastAPI:
    api_key = os.environ["INFRAI_API_KEY"]
    client = InfraiClient(api_key)
    search = ContentSearch(client, os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await client.close()

    app = FastAPI(title="Creator Commerce Search", lifespan=lifespan)

    @app.post("/content/index")
    async def index_content(request: IndexRequest) -> dict[str, int]:
        try:
            return {"indexed": await search.index(request.collection, request.items)}
        except InfraiError as error:
            raise HTTPException(status_code=_client_status(error), detail=error.detail) from error

    @app.post("/content/search", response_model=SearchResponse)
    async def search_content(request: SearchRequest) -> SearchResponse:
        try:
            hits = await search.search(
                request.collection, request.query, request.creator_id, request.top_k
            )
            return SearchResponse(hits=hits)
        except InfraiError as error:
            raise HTTPException(status_code=_client_status(error), detail=error.detail) from error

    return app


def _client_status(error: InfraiError) -> int:
    return error.status_code if 400 <= error.status_code < 500 else 502


app = build_app()
