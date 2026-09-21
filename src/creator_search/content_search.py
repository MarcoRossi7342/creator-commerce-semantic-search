from typing import Any

from creator_search.models import CreatorContent, SearchHit


class ContentSearch:
    def __init__(self, backend: Any, embedding_model: str) -> None:
        self._backend = backend
        self._embedding_model = embedding_model

    async def index(self, collection: str, items: list[CreatorContent]) -> int:
        vectors: list[dict[str, Any]] = []
        for item in items:
            embedding = await self._backend.embed(self._document_text(item), self._embedding_model)
            vectors.append(
                {
                    "id": item.content_id,
                    "values": embedding,
                    "metadata": item.model_dump(exclude={"body"}),
                }
            )
        await self._backend.create_collection(collection, len(vectors[0]["values"]))
        await self._backend.upsert(collection, vectors)
        return len(vectors)

    async def search(
        self, collection: str, query: str, creator_id: str, top_k: int
    ) -> list[SearchHit]:
        embedding = await self._backend.embed(query, self._embedding_model)
        result = await self._backend.query(collection, embedding, creator_id, top_k)
        return [self._to_hit(match) for match in result.get("matches", [])]

    @staticmethod
    def _document_text(item: CreatorContent) -> str:
        return f"{item.kind}\n{item.title}\n{item.body}"

    @staticmethod
    def _to_hit(match: dict[str, Any]) -> SearchHit:
        metadata = match["metadata"]
        kind = metadata["kind"]
        return SearchHit(
            content_id=str(match["id"]),
            score=float(match["score"]),
            kind=kind,
            title=str(metadata["title"]),
            next_action="open_download" if kind == "digital_asset_delivery" else "read_update",
        )
