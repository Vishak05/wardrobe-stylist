# AI Wardrobe Stylist — Project Context

Technical brief for this project: architecture, schema, stack, code conventions, and environment specifics. This is a reference document, not a status report — consult the actual codebase to determine what currently exists.

## Repo

- **Structure**: Monorepo, GitHub repo `wardrobe-stylist`
- **Root**: `wardrobe-stylist/`
  - `wardrobe-backend/` — FastAPI + Celery backend
  - `wardrobe-frontend/` — React Native/Expo app
- Single Python venv at repo root (`wardrobe-stylist/venv`), activated when working in `wardrobe-backend/`
- Python **3.11** (deliberately avoids 3.14+ due to native-extension wheel availability for pydantic-core, torch, onnxruntime, transformers)
- Git via GitHub Desktop. `.gitignore` excludes `venv/`, `.env`, `__pycache__/`, `node_modules/`
- `.env.example` is committed (template); `.env` is not (real secrets/local config)

## Person's background (for calibrating explanations/code style)

Final-year CS student, strong practical background: JavaScript, React, Angular, concurrent programming, ML/digital image processing. Treat as a capable peer — no fundamentals explanations needed. Prefers highly technical, concise, production-grade responses. Values understanding *why*, not just *what* — explain concepts (SQLAlchemy internals, Pydantic mechanics, async patterns, etc.) inline while writing code, not separately. Favors targeted changes over rewrites. Uses conventional commit message format.

---

## System Architecture

Computer-vision-driven wardrobe digitization + LLM/RAG-based outfit recommendation.

### Workflow A: Image Ingestion (Asynchronous)

1. Core API receives raw image upload → saves to blob storage → creates `pending` DB record → pushes task to queue → returns `202 Accepted`
2. Vision Worker (Celery) consumes task, runs background segmentation to isolate garment (`rembg`)
3. Vision Worker extracts features (category, sub-category, color, pattern) via a vision model
4. Vision Worker generates a dense vector embedding of the item's style (SigLIP or CLIP via `transformers`)
5. Vision Worker commits metadata to PostgreSQL, embedding to pgvector column, notifies client, sets status to `completed`

### Workflow B: Recommendation Pipeline (RAG)

1. Core API parses natural language query
2. Backend pre-filters PostgreSQL (`user_id` + `status=completed`) to retrieve relevant wardrobe items, saving LLM context
3. Backend formats prompt with query + filtered JSON wardrobe array
4. LLM call enforces strict JSON structured output returning exact `item_id`s (Gemini `response_schema`)
5. Backend fetches corresponding image URLs, returns finalized outfit payload

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async, `Mapped[]`/`mapped_column` style) |
| DB | PostgreSQL 16 + pgvector extension |
| DB driver | psycopg3 (async-native, NOT psycopg2/asyncpg) |
| Validation | Pydantic v2 |
| Migrations | Alembic |
| LLM | Google Gemini (`google-genai` SDK), model `gemini-3.6-flash` |
| Task queue | Celery + Redis |
| Background removal | `rembg` |
| Embedding model | SigLIP or CLIP via `transformers` |
| Frontend | React Native (Expo), `expo-camera` |
| Containerization | Docker Compose (Postgres, Redis) |

Note on Gemini model naming: `gemini-2.5-flash` was deprecated/retired for new users as of ~August 2026 (full shutdown October 2026). Currently using `gemini-3.6-flash`. Model strings deprecate on a real cadence — check `https://ai.google.dev/gemini-api/docs/models` if a `404 NOT_FOUND` / "no longer available" error appears on the Gemini call.

---

## Database Schema

`models/orm.py`:

```python
EMBEDDING_DIM = 768  # SigLIP base assumption — MUST match whatever embedding model the worker actually uses

class Base(DeclarativeBase):
    pass

class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class GarmentCategory(str, enum.Enum):
    TOP = "top"
    BOTTOM = "bottom"
    OUTERWEAR = "outerwear"
    DRESS = "dress"
    FOOTWEAR = "footwear"
    ACCESSORY = "accessory"

class WardrobeItemORM(Base):
    __tablename__ = "wardrobe_items"

    item_id: Mapped[uuid.UUID]            # PK, default uuid4
    user_id: Mapped[uuid.UUID]            # indexed, no FK (no auth system — opaque UUID)
    raw_image_url: Mapped[str]            # not null
    processed_image_url: Mapped[str | None]  # set by worker post-rembg

    status: Mapped[IngestionStatus]       # not null, default PENDING, indexed
    failure_reason: Mapped[str | None]

    category: Mapped[GarmentCategory | None]   # nullable — set by worker
    sub_category: Mapped[str | None]
    primary_color: Mapped[str | None]
    secondary_color: Mapped[str | None]
    pattern: Mapped[str | None]
    fit: Mapped[str | None]
    material: Mapped[str | None]
    season_tags: Mapped[list[str] | None]  # JSONB

    style_embedding: Mapped[list[float] | None]  # pgvector Vector(768), nullable

    created_at: Mapped[datetime]  # server_default=func.now()
    updated_at: Mapped[datetime]  # onupdate=func.now()

    # Indexes: IVFFlat (style_embedding, vector_cosine_ops, lists=100),
    #          composite btree (user_id, category),
    #          single-column btree on category and status (from index=True)
```

**Operational note**: IVFFlat index quality depends on cluster centroids computed at build time from whatever data exists then. If the index was built against a near-empty/seed-only table, plan a `REINDEX` once realistic data volume exists — don't trust ANN recall quality until then.

### Pydantic Schemas — `schemas/wardrobe.py`

- `WardrobeItemCreate` — inbound at ingestion (`user_id`, `raw_image_url`). Note: assumes a pre-existing URL — the real multipart-upload ingestion endpoint will need a different inbound shape (`UploadFile`, not a URL string).
- `WardrobeItemIngestAck` — 202 response body (`item_id`, `status`)
- `WardrobeItem` — general read model, `ConfigDict(from_attributes=True)`, excludes embedding
- `WardrobeItemInternal(WardrobeItem)` — adds `style_embedding`, has a `field_validator` enforcing `len == EMBEDDING_DIM`. Worker-internal only, never a FastAPI `response_model`.
- `WardrobeItemLLMView` — minimal projection for LLM context (item_id, category, sub_category, primary_color, pattern, fit, season_tags). Requires `ConfigDict(from_attributes=True)` for `.model_validate(orm_instance)` to work — easy to forget on new projection models, causes a `ValidationError` if omitted.

### `schemas/outfit.py`

- `OutfitRequest` — `user_id`, `query` (free text), optional `occasion`, `max_temperature_celsius`
- `LLMOutfitSelection` — the exact `response_schema` passed to Gemini: `item_ids: list[UUID]`, `styling_notes: str`
- `OutfitResponse` — client-facing: `item_ids`, `styling_notes`, `image_urls: dict[UUID, str]`

---

## Recommendation Endpoint

`routers/recommendations.py` — `POST /recommendations`:

```python
@router.post("", response_model=OutfitResponse)
async def create_recommendation(request: OutfitRequest, db: AsyncSession = Depends(get_db)):
    # 1. Pre-filter: user_id + status == COMPLETED only (deliberately conservative —
    #    relies on LLM semantic reasoning over the full filtered set rather than
    #    rigid SQL filtering by category/season/occasion)
    # 2. Project filtered ORM rows -> WardrobeItemLLMView
    # 3. Call Gemini via services/gemini_client.py
    # 4. Validate: selection.item_ids must be subset of the filtered set's item_ids
    #    (defense against hallucination — response_schema guarantees structural
    #    validity, NOT that IDs were actually in the provided list)
    # 5. Resolve item_id -> processed_image_url (fallback raw_image_url), return OutfitResponse
```

`services/gemini_client.py`:

```python
client = genai.Client(api_key=settings.gemini_api_key)

async def get_outfit_recommendation(query: str, wardrobe_items: list[WardrobeItemLLMView]) -> LLMOutfitSelection:
    response = await client.aio.models.generate_content(
        model="gemini-3.6-flash",
        contents=[f"User request: {query}", f"Available wardrobe items: {wardrobe_json}"],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=LLMOutfitSelection,
        ),
    )
    return response.parsed
```

Uses `client.aio` (async namespace) since the endpoint is `async def` — a sync call would block the event loop.

---

## `database.py` — async session setup

```python
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

`settings.database_url` uses `postgresql+psycopg://...` (psycopg3, supports both sync and async — Alembic uses the sync path internally, FastAPI uses async via this file).

---

## Environment / Infra

`docker-compose.yml` (at `wardrobe-backend/`):

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: wardrobe
      POSTGRES_PASSWORD: wardrobe_dev
      POSTGRES_DB: wardrobe_db
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
volumes:
  pgdata:
```

Consider `restart: unless-stopped` on both services — containers not surviving reboot has caused silent "everything hangs, no error" symptoms before (TCP connect attempts to a dead port on Windows can hang rather than fail fast).

`.env` (not committed):
```
DATABASE_URL=postgresql+psycopg://wardrobe:wardrobe_dev@localhost:5432/wardrobe_db
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=<real key>
```

`config.py` uses `pydantic-settings` `BaseSettings` reading from `.env`.

### Environment gotchas specific to this setup (Windows + Docker + psycopg3 async)

1. **Native PostgreSQL service on Windows can conflict with port 5432.** If a native Postgres install exists (e.g. as a Windows service `postgresql-x64-*`), it can intercept connections meant for the Docker container, producing "password authentication failed" even with correct Docker credentials (since a *different* Postgres process is answering). Check `Get-Service | Where-Object {$_.Name -like "*postgres*"}` if auth errors don't make sense given known-correct credentials.
2. **Docker named-volume persistence**: `POSTGRES_USER`/`POSTGRES_PASSWORD` env vars are only applied by the Postgres image on first initialization against an empty data directory. Changing them in `docker-compose.yml` later does nothing if the volume already has an initialized cluster. Fix: `docker compose down -v` (the `-v` removes the volume) then `up -d`.
3. **Windows async event loop incompatibility**: `psycopg` async mode does not work with Windows' default `ProactorEventLoop`. Any standalone async script (outside uvicorn, which handles this internally) needs, before any asyncio usage:
   ```python
   if sys.platform == "win32":
       asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
   ```
4. **Alembic + pgvector autogenerate gaps**: autogenerate does not add `import pgvector.sqlalchemy` to generated migration files even though it references `pgvector.sqlalchemy.vector.VECTOR(...)` in the generated code — add manually. It also does not add `CREATE EXTENSION IF NOT EXISTS vector` — add manually to `upgrade()`, with a corresponding `DROP EXTENSION` in `downgrade()`.
5. **pip install failures on very new Python versions**: native-extension packages (pydantic-core, torch, onnxruntime) may lack prebuilt wheels for a just-released Python version, causing pip to fall back to a source build that fails without a Rust/C toolchain. Stay on Python 3.11 for this project.

---

## File Structure

```
wardrobe-stylist/
├── venv/                          # single shared venv, gitignored
├── .gitignore
├── wardrobe-backend/
│   ├── .env                       # gitignored, real secrets
│   ├── .env.example               # committed template
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── config.py                  # pydantic-settings
│   ├── database.py                # async engine/session
│   ├── main.py                    # FastAPI app entrypoint
│   ├── alembic.ini
│   ├── models/
│   │   ├── __init__.py
│   │   └── orm.py                 # WardrobeItemORM, enums, Base
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── wardrobe.py            # WardrobeItem* Pydantic models
│   │   └── outfit.py              # OutfitRequest/Response, LLMOutfitSelection
│   ├── services/
│   │   ├── __init__.py
│   │   └── gemini_client.py       # Gemini structured-output call
│   ├── routers/
│   │   ├── __init__.py
│   │   └── recommendations.py     # POST /recommendations
│   ├── scripts/
│   │   └── seed_data.py           # manual test data (fake wardrobe items)
│   └── migrations/
│       ├── env.py                 # imports Base, sets target_metadata
│       └── versions/
└── wardrobe-frontend/
```

### requirements.txt

```
fastapi==0.115.*
uvicorn[standard]==0.32.*
sqlalchemy==2.0.*
pgvector==0.3.*
psycopg[binary]==3.2.*
pydantic==2.9.*
pydantic-settings==2.6.*
alembic==1.13.*
google-genai==1.*
```

---

## Design Decisions & Rationale

- **Every Pydantic model boundary is deliberate and separate** — never one model with everything `Optional`. `WardrobeItem` (API-facing) vs. `WardrobeItemInternal` (worker-only, has embedding) vs. `WardrobeItemLLMView` (minimal LLM-context projection) are intentionally distinct contracts serving different boundaries, not DRY violations to consolidate.
- **SQLAlchemy 2.0 typed declarative style** (`Mapped[X]` + `mapped_column(...)`) throughout — not legacy `Column()`.
- **Async end-to-end on the API request path** (async engine, async Gemini client via `client.aio`) — sync is only acceptable for one-off scripts and Alembic, which run outside the request/response cycle.
- **psycopg3, not psycopg2 or asyncpg** — chosen specifically because it supports both sync and async from one driver, avoiding a driver split between Alembic (sync) and FastAPI (async).
- **Pre-filtering in the recommendation endpoint is deliberately conservative** (only `user_id` + `status`) — relies on the LLM's semantic reasoning over the full filtered wardrobe rather than rigid SQL filters by category/season/occasion, since rigid filters risk excluding items that are contextually valid in ways a SQL `WHERE` clause can't capture (e.g. a blazer fitting both "business casual" and "date night").
- **`EMBEDDING_DIM = 768`** is a hard constraint tying the DB schema to whichever embedding model the vision worker uses — any change to the embedding model choice must keep output dimension at 768, or the column type/migration needs to change first.
- **No auth/user management system** — `user_id` is an opaque UUID throughout, no FK constraint, no login flow.
- **Dev/test utility scripts live in `scripts/`**, not project root, to keep the distinction between "the application" and "tooling" clear.
- **Conventional commit messages** (`feat:`, `fix:`, etc.).
- **Blob storage provider is not yet decided** — needed for the real ingestion endpoint to have somewhere to write `raw_image_url`/`processed_image_url` to.
- **Feature-extraction approach for the vision worker is not yet decided** — candidates are another Gemini multimodal call (consistent with existing stack) or a dedicated vision model.
