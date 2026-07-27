# RAGFlow

Enterprise-grade AI Knowledge Assistant — RAG platform with hybrid search, multi-model routing,
workspaces, and observability. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design.

## What's here (base scaffold)

- `backend/` — FastAPI app: config, DB models, LLM gateway, ingestion + retrieval services,
  Celery workers, auth/documents/chat routes (Phase 1 shape, several TODOs to wire real logic)
- `frontend/` — Next.js app: streaming chat page, upload API client, Tailwind setup
- `infra/docker-compose.yml` — Postgres+pgvector, Redis, MinIO, backend, worker, frontend
- `docs/ARCHITECTURE.md` — system design, data model, retrieval pipeline, roadmap

## Quickstart (local dev)

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# fill in OPENAI_API_KEY / ANTHROPIC_API_KEY etc.

# 2. Start everything
cd infra
docker compose up --build

# Backend:  http://localhost:8000/health
# Frontend: http://localhost:3000
# MinIO console: http://localhost:9001 (ragflow / ragflow123)
```

## First implementation tasks (in order)

The scaffold intentionally raises `NotImplementedError` at the real work — this is the punch list:

1. **DB migrations** — run `alembic init` in `backend/alembic`, generate the initial migration from
   `app/models/*`, enable the `vector` extension in the migration.
2. **Auth** — implement `app/api/v1/routes/auth.py` (bcrypt hashing, JWT issuance) and a
   `get_current_user` dependency used by protected routes.
3. **Ingestion** — implement `extract_text()` in `app/services/ingestion.py` for PDF/DOCX/TXT/MD first;
   wire `process_document()` to actually read/write the `Document`/`Chunk` rows.
4. **Embeddings + retrieval** — implement `OpenAIProvider.embed()` in `app/core/llm_gateway.py`, then
   `vector_search()` in `app/services/retrieval.py` (pgvector `<=>` query).
5. **Chat** — implement `OpenAIProvider.stream_chat()`, confirm `/api/v1/chat/stream` streams real
   tokens end-to-end into the Next.js chat page.
6. **Workspaces & documents CRUD** — round out the routes marked `501 Not yet implemented`.

Once (1)-(6) work end to end, move to Phase 2 in `docs/ARCHITECTURE.md` §10 (hybrid search, RBAC,
OAuth, collections, admin dashboard).

## Repo layout

See `docs/ARCHITECTURE.md` §4 for the annotated layout and the reasoning behind it.
