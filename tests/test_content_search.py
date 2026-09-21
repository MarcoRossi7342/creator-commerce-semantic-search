import asyncio
from typing import Any

from creator_search.content_search import ContentSearch


class StubBackend:
    def __init__(self) -> None:
        self.query_embedding: list[float] = []

    async def embed(self, text: str, model: str) -> list[float]:
        return [0.2, 0.8]

    async def create_collection(self, collection: str, dimension: int) -> None:
        return None

    async def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> None:
        return None

    async def query(
        self, collection: str, embedding: list[float], creator_id: str, top_k: int
    ) -> dict[str, Any]:
        self.query_embedding = embedding
        return {
            "matches": [
                {
                    "id": "asset-color-pack",
                    "score": 0.94,
                    "metadata": {
                        "kind": "digital_asset_delivery",
                        "title": "Autumn color grading pack",
                    },
                },
                {
                    "id": "update-september",
                    "score": 0.71,
                    "metadata": {
                        "kind": "subscriber_update",
                        "title": "September studio note",
                    },
                },
            ]
        }


def test_search_hands_embedding_to_vector_query_and_selects_next_action() -> None:
    backend = StubBackend()
    service = ContentSearch(backend, "embedding-model")

    hits = asyncio.run(service.search("content", "warm color download", "creator-42", 2))

    assert backend.query_embedding == [0.2, 0.8]
    assert [hit.next_action for hit in hits] == ["open_download", "read_update"]
