import asyncio
import os

from creator_search.content_search import ContentSearch
from creator_search.infrai_client import InfraiClient
from creator_search.models import CreatorContent


async def main() -> None:
    client = InfraiClient(os.environ["INFRAI_API_KEY"])
    search = ContentSearch(client, os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    try:
        await search.index(
            "creator-content-demo",
            [
                CreatorContent(
                    content_id="asset-color-pack",
                    creator_id="creator-42",
                    kind="digital_asset_delivery",
                    title="Autumn color grading pack",
                    body="Download the LUT archive and setup notes for warm outdoor footage.",
                ),
                CreatorContent(
                    content_id="update-september",
                    creator_id="creator-42",
                    kind="subscriber_update",
                    title="September studio note",
                    body="A short production diary covering lights, lenses, and the next release.",
                ),
            ],
        )
        hits = await search.search(
            "creator-content-demo", "Where is my warm color download?", "creator-42", 3
        )
        for hit in hits:
            print(hit.model_dump_json())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
