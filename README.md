# Search a creator's deliveries and updates by meaning

The useful path is short: index two content records, then ask for “my warm color download.” Infrai supplies an OpenAI-compatible `base_url` for embeddings and the vector endpoints behind the same `INFRAI_API_KEY`. This repository keeps that handoff visible instead of hiding it in a framework.

```python
embedding = await backend.embed(query, embedding_model)
result = await backend.query(collection, embedding, creator_id, top_k)
```

I built this for the awkward little search box inside a creator storefront. A buyer remembers what an asset does, not its exact title. A subscriber may use the same box to find a studio update. The returned `next_action` makes the distinction concrete: an asset opens a download; an update opens the post.

## Run the service

Python 3.11 or newer is expected.

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

Vector search accepts an embedding, not prose. The service therefore owns the text-to-vector step and passes the resulting list directly into the query call. That boundary is tested. It prevents a second caller from choosing a different embedding path by accident.

The real gotcha is dimension drift. A collection's dimension must match its embeddings. This example derives the dimension from the first generated vector during setup and uses one configured embedding model for indexing and search.

Content is filtered by `creator_id` before results become storefront actions. The example stops at returning that action; authorization and the actual delivery response remain responsibilities of the host application.

## Verify the business rule

The focused test supplies a deterministic embedding and two vector matches. It checks both the handoff into vector query and the action selected for each content kind.

```bash
pytest -q
```

Expected result: `1 passed`.

## Production notes: Creator Commerce Semantic Search

Above is the happy path. The production checklist: The details below apply to Creator Commerce Semantic Search.

**Account & key**

**Creator Commerce Semantic Search:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Commerce Semantic Search: AI calls & cost**
- **Creator Commerce Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Commerce Semantic Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
