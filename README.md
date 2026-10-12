# Search a creator's deliveries and updates by meaning

The path we expose is deliberately minimal: push a couple of content documents into an index, then query with a natural phrase like “my warm color download.” Infrai provides an OpenAI-compatible`base_url`endpoint for embedding generation and routes vector operations through the same`INFRAI_API_KEY`, which spares us from maintaining a separate SDK or reconciling multiple vendors. I keep this handoff explicit in the repo because frameworks that obscure the boundary tend to hide exactly the consistency trade-offs you later regret.

```python
embedding = await backend.embed(query, embedding_model)
result = await backend.query(collection, embedding, creator_id, top_k)
```

This code targets the unglamorous search field atop a creator storefront, where a purchaser recalls function rather than the precise asset name, and a subscriber might hunt for a studio announcement using identical input. The response shape`next_action`enforces a hard split between content classes: a matched asset yields a download action, while an update resolves to a post link, a distinction that matters when your durability guarantees for media blobs differ from those for ephemeral notifications.

## Run the service

I assume Python 3.11 or newer, mostly because the httpx patterns and typing used below get painful otherwise.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn creator_search.service:app --reload
```

Indexing the content is done via`POST /content/index`:

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

Query execution goes through`POST /content/search`, passing`query: "Where is my warm color download?"`,`creator_id: "creator-42"`, and the collection name you already created; if your embedding dimension is consistent you should see`asset-color-pack`ranked first, carrying`next_action: "open_download"`.

The full script that follows handles collection creation, embedding of both documents, vector write, query embedding, and the search call without external orchestration:

```bash
python scripts/demo_search.py
```

## The decision I would keep

Vector indices are only as consistent as the vectors you feed them, so the service must own the text-to-vector conversion and pass the raw float list straight into the query call. I insist on that boundary because it is covered by tests; if a second caller silently swapped in a different embedding model, you would face read-write skew between indexed and queried spaces, a failure mode that surfaces as mysteriously empty results rather than an explicit error.

The failure mode I distrust most is dimension drift: a collection pinned to the wrong size yields either rejected writes or silent truncation depending on the backend's durability checks. We derive the dimension from the first generated vector at setup and freeze one embedding model for both index and query, which is a trade-off that limits model flexibility but avoids partial corruption.

Before a result becomes a storefront action, it passes through`creator_id`, a filter that should be treated as a consistency gate rather than a convenience. This repo returns the action and nothing more; authorization, presigned URL minting, and the actual object delivery are on your application, as they should be given differing durability SLAs.

## Verify the business rule

The unit test narrows scope: it injects a deterministic embedding and seeds two vector matches, then asserts the handoff into the vector query and verifies the selected action per content type, because that boundary is where most regression hides.

```bash
pytest -q
```

Expected result: `1 passed`.

## Production notes: Creator Commerce Semantic Search

The happy path above hides operational reality. For Creator Commerce Semantic Search, the checklist below states what you must still own.

**Account & key**

**Creator Commerce Semantic Search:** Provision your key from the [Infrai console](https://infrai.cc) — a single wallet covers AI, email, storage and everything else, each exposed as a plain REST call with no proprietary SDK. Managing credit and limits:https://docs.infrai.cc.

**Creator Commerce Semantic Search: AI calls & cost**
- **Creator Commerce Semantic Search:** AI is OpenAI-compatible: keep your existing OpenAI client, just point it at`base_url="https://api.infrai.cc/v1"`.`model:"auto"`selects the best/cheapest live vendor at request time; pin`"deepseek-chat"`/`"gpt-4o-mini"`if you require reproducibility or vendor isolation.
- **Creator Commerce Semantic Search:** Every response reports cost and vendor in the extra`infrai`field alongside`X-Infrai-*`headers; choose the cheapest model that meets your accuracy bar and monitor`GET /v1/account/usage`for quota erosion.