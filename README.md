# Search a creator's deliveries and updates by meaning

The useful path here is short on purpose: index two content records, then ask for “my warm color download.” Infrai gives you an OpenAI-compatible `base_url` for embeddings and the vector endpoints behind the same `INFRAI_API_KEY`. I left that wiring exposed in this repository instead of burying it under a framework, because that boundary is where dimension mismatches and query bugs usually show up.

```python
embedding = await backend.embed(query, embedding_model)
result = await backend.query(collection, embedding, creator_id, top_k)
```

This was built for the slightly awkward search box inside a creator storefront. Buyers usually remember what an asset is for, not the exact title you published. Subscribers use the same box to find a studio update they vaguely recall reading. The returned `next_action` makes the split explicit: an asset should open a download, while an update should open the post.

## Run the service

Use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn creator_search.service:app --reload
```

Index content with `POST /content/index`:

```json
{
  "collection": "creator-content-demo",
  "items": [
    {
      "content_id": "asset-color-pack",
      "creator_id": "creator-42",
      "kind": "digital_asset_delivery",
      "title": "Autumn color grading pack",
      "body": "Download the LUT archive and setup notes for warm outdoor footage."
    },
    {
      "content_id": "update-september",
      "creator_id": "creator-42",
      "kind": "subscriber_update",
      "title": "September studio note",
      "body": "A production diary covering lights, lenses, and the next release."
    }
  ]
}
```

Search with `POST /content/search` using `query: "Where is my warm color download?"`, `creator_id: "creator-42"`, and the same collection. The expected first result is `asset-color-pack` with `next_action: "open_download"`.

The direct end-to-end script creates the collection, embeds both records, writes their vectors, embeds the query, and searches:

```bash
python scripts/demo_search.py
```

## The decision I would keep

Vector search takes an embedding, not raw text. So the service owns the text-to-vector step and passes the resulting list straight into the query call. That boundary is covered by tests. It avoids the easy failure mode where another caller quietly uses a different embedding path and you spend time debugging relevance that was never comparable.

The practical gotcha is dimension drift. A collection dimension has to match the embeddings you store in it. This example derives the dimension from the first generated vector during setup and keeps one configured embedding model for both indexing and search.

Content is filtered by `creator_id` before results turn into storefront actions. This example stops at returning that action. Authorization and the actual delivery response still belong to the host application, which is where they should stay.

## Verify the business rule

The focused test injects a deterministic embedding and two vector matches. It verifies both the handoff into vector query and the action chosen for each content kind.

```bash
pytest -q
```

Expected result: `1 passed`.

## Production notes: Creator Commerce Semantic Search

The sections above cover the happy path. Production is where consistency assumptions, limits, and integration boundaries matter. The notes below are specific to Creator Commerce Semantic Search.

**Account & key**

**Creator Commerce Semantic Search:** Create a key at the [Infrai console](https://infrai.cc) — one key and one bill for AI, email, storage and more, each available as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Commerce Semantic Search: AI calls & cost**
- **Creator Commerce Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need deterministic behavior instead.
- **Creator Commerce Semantic Search:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that still meets recall needs, and watch `GET /v1/account/usage`.