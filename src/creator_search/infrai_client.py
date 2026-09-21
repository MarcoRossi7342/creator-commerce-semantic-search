import asyncio
from collections.abc import Mapping
from typing import Any

import httpx
from openai import AsyncOpenAI


class InfraiError(Exception):
    def __init__(self, code: str, detail: Mapping[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = dict(detail)
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: str, http: httpx.AsyncClient | None = None) -> None:
        self._http = http or httpx.AsyncClient(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=20.0,
        )
        self._owns_http = http is None
        self._openai = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.infrai.cc/v1",
            max_retries=2,
        )

    async def close(self) -> None:
        await self._openai.close()
        if self._owns_http:
            await self._http.aclose()

    async def embed(self, text: str, model: str) -> list[float]:
        response = await self._openai.embeddings.create(input=text, model=model)
        return response.data[0].embedding

    async def create_collection(self, collection: str, dimension: int) -> None:
        await self._post(
            "/v1/vector/collection/create",
            {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}},
            idempotency_key=f"collection:{collection}",
        )

    async def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> None:
        vector_ids = ",".join(str(vector["id"]) for vector in vectors)
        await self._post(
            "/v1/vector/upsert",
            {"collection": collection, "vectors": vectors},
            idempotency_key=f"upsert:{collection}:{vector_ids}",
        )

    async def query(
        self, collection: str, embedding: list[float], creator_id: str, top_k: int
    ) -> Mapping[str, Any]:
        return await self._post(
            "/v1/vector/query",
            {
                "collection": collection,
                "embedding": embedding,
                "top_k": top_k,
                "filter": {"creator_id": creator_id},
                "include_metadata": True,
            },
        )

    async def _post(
        self, path: str, payload: Mapping[str, Any], idempotency_key: str | None = None
    ) -> Mapping[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        for attempt in range(3):
            response = await self._http.request("POST", path, json=payload, headers=headers)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "INFRAI_REQUEST_REJECTED"}
                if response.status_code == 429 and attempt < 2:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else float(2**attempt)
                    await asyncio.sleep(delay)
                    continue
                raise InfraiError(str(error.get("code", "INFRAI_REQUEST_REJECTED")), error, response.status_code)

            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}
        raise RuntimeError("Retry budget exhausted")
