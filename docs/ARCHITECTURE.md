# RAGFlow — Base Architecture & Documentation

Version: 0.1 (MVP baseline)
Status: Draft for implementation kickoff

---

## 1. What we're building first

The full spec is enterprise-scale (multi-tenant workspaces, hybrid search, OCR, audio/video ingestion,
multi-model routing, observability, admin dashboards, integrations). Building all of it at once is how
these projects die. This document defines a **base architecture** that:

- Is structurally ready for every feature in the spec (nothing needs a rewrite later)
- Ships a working vertical slice first: upload → chunk → embed → search → chat → cite
- Lets you bolt on OCR, hybrid search, routing, observability, etc. as independent modules

**MVP scope (Phase 1):** single embedding model, single LLM provider, Postgres+pgvector only (no BM25 yet),
PDF/DOCX/TXT/MD upload, one workspace per org, email auth, streaming chat with citations.
Everything else in the spec becomes Phase 2+ (see §10).

---

## 2. System overview

```
                                   ┌─────────────────────────┐
                                   │        Next.js UI        │
                                   │  (chat, upload, admin)   │
                                   └────────────┬─────────────┘
                                                │ HTTPS / SSE
                                   ┌────────────▼─────────────┐
                                   │       FastAPI (API)       │
                                   │  auth · workspaces · chat │
                                   │  documents · search · admin│
                                   └───┬───────────┬───────────┘
                          enqueue job  │           │ query
                        ┌──────────────▼──┐   ┌────▼─────────────┐
                        │  Redis (broker +  │   │  Retrieval layer  │
                        │  cache)           │   │  (hybrid search,  │
                        └───────┬───────────┘   │  re-rank, prompt) │
                                │               └────┬──────────────┘
                     ┌──────────▼──────────┐         │
                     │  Celery workers      │         │ vector + metadata
                     │  (extract → chunk →  │         │
                     │   embed → index)     │◄────────┘
                     └──────────┬───────────┘
                                │
                  ┌─────────────▼─────────────┐      ┌───────────────────┐
                  │ PostgreSQL + pgvector      │      │ Object storage     │
                  │ (docs, chunks, vectors,    │      │ (MinIO / S3)       │
                  │  chats, users, workspaces) │      │ raw files          │
                  └────────────────────────────┘      └───────────────────┘

        Cross-cutting: LLM Gateway (provider abstraction) · Observability (Langfuse/OTel) · Auth (JWT/OAuth)
```

**Why this shape:**
- **API and workers are separate processes from day one.** Document processing (OCR, transcription,
  embedding) is slow and bursty; it must never block request/response threads. This also means
  Phase-2 ingestion types (audio/video/website/YouTube) just add new Celery task types, not new services.
- **A dedicated "LLM Gateway" module** wraps every provider (OpenAI, Claude, Gemini, Ollama) behind one
  interface, so model routing/switching is a config change, not a rewrite.
- **A dedicated "Retrieval" module** wraps vector search, keyword search, filtering, and re-ranking behind
  one interface, so hybrid search (Phase 2) slots in without touching the chat endpoint.

---

## 3. Technology stack (base, not aspirational)

| Layer | Choice | Notes |
|---|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui | React Query for server state, Framer Motion for transitions |
| API | FastAPI (Python 3.11+) | async throughout; Pydantic v2 schemas |
| Orchestration | LangGraph + LangChain | LangGraph for the retrieval→generation state machine; LangChain for provider/loader glue only |
| DB | PostgreSQL 16 + pgvector | one database, vectors live next to their metadata (no separate vector DB to sync) |
| Cache/Broker | Redis | Celery broker + result backend + response/embedding cache |
| Background jobs | Celery | worker pool separate from API pool |
| Object storage | MinIO (dev) / S3 (prod) — same API | raw files, never store binaries in Postgres |
| Auth | JWT (access + refresh) via FastAPI + OAuth (Google/GitHub) | RBAC via a `role` on workspace membership, not on the user globally |
| Observability | Langfuse (self-hosted or cloud) | traces prompts, retrieved chunks, latency, cost per call |
| Deployment | Docker Compose (dev) → same images on ECS/K8s (prod) | one Dockerfile per service, no dev/prod drift |

---

## 4. Monorepo layout

```
ragflow/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/       # thin HTTP layer only (auth, workspaces, documents, chat, search, admin)
│   │   ├── core/                # config, security, dependencies, LLM gateway, exceptions
│   │   ├── db/                  # session, base, migrations (alembic)
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response models
│   │   ├── services/             # business logic: ingestion, chunking, embeddings, retrieval, chat
│   │   ├── workers/              # celery app + tasks (process_document, transcribe, crawl_website...)
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/                     # Next.js routes: (auth), (workspace)/[id]/chat, /admin
│   ├── components/
│   ├── lib/                     # api client, auth helpers, sse client
│   ├── Dockerfile
│   └── package.json
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── .github/workflows/ci.yml
└── docs/
    ├── ARCHITECTURE.md          # this file
    ├── DATA_MODEL.md
    └── ROADMAP.md
```

**Rule of thumb enforced by this layout:** routes never contain business logic. Routes validate input,
call a service, return the service's result. This is what makes swapping embedding models, adding
hybrid search, or adding a new ingestion type a change to one `service`, not a hunt through the codebase.

---

## 5. Core data model

```
organizations
  id, name, plan, created_at

workspaces
  id, org_id → organizations, name, created_at

workspace_members
  id, workspace_id → workspaces, user_id → users, role (admin | editor | viewer)

users
  id, email, hashed_password (nullable if OAuth-only), name, created_at

oauth_accounts
  id, user_id → users, provider (google | github), provider_account_id

documents
  id, workspace_id → workspaces, collection_id (nullable) → collections
  filename, file_type, storage_path, status (pending | processing | ready | failed)
  author, tags[], department, version, parent_document_id (nullable, for versioning)
  uploaded_by → users, created_at

collections
  id, workspace_id → workspaces, name, description

chunks
  id, document_id → documents
  content, embedding (vector(N)), page_number, paragraph_index
  chunk_strategy (fixed | semantic | parent_child), parent_chunk_id (nullable)

conversations
  id, workspace_id → workspaces, user_id → users, title, created_at

messages
  id, conversation_id → conversations, role (user | assistant), content
  citations (jsonb: [{document_id, page, paragraph, score}]), created_at

feedback
  id, message_id → messages, rating (up | down), comment (nullable)

api_usage_log
  id, workspace_id, provider, model, input_tokens, output_tokens, cost_usd, latency_ms, created_at
```

Key decisions:
- **`chunks.embedding` uses pgvector's `vector` type** with an IVFFlat or HNSW index — no separate vector
  store to keep in sync with metadata.
- **Versioning is a self-reference** (`parent_document_id`), not a separate table — keeps diffing simple.
- **RBAC lives on `workspace_members.role`**, not on the user — a user can be Editor in one workspace and
  Viewer in another, matching the spec's workspace model.

---

## 6. Retrieval pipeline (the part that must be right)

```
1. User question arrives with workspace_id (+ optional collection_id, filters)
2. Embed the question (same embedding model the workspace's chunks were embedded with)
3. Hybrid search:
     a. Vector search (pgvector cosine similarity) — top K
     b. Keyword search (Postgres full-text / BM25-style ts_rank) — top K
     c. Merge + de-duplicate (reciprocal rank fusion)
     d. Apply metadata filters (file, author, date, tags) BEFORE fusion, not after
4. Re-rank merged candidates (cross-encoder or LLM-based re-rank) → top N
5. Build prompt: system instructions + retrieved chunks (with source labels) + chat history summary
6. Route to model (see §7) and stream the response
7. Parse citations from the chunks actually used → attach to message
8. Persist message + citations + usage metrics
```

This is implemented as a LangGraph graph with explicit nodes (`embed_query`, `search`, `rerank`,
`build_prompt`, `generate`, `extract_citations`) so each step is independently testable and swappable —
this is where hybrid search, re-ranking model changes, and prompt versioning all plug in later without
touching the API layer.

---

## 7. Multi-model support (LLM Gateway)

A single interface, one adapter per provider:

```python
class LLMProvider(Protocol):
    async def stream_chat(self, messages: list[Message], **kwargs) -> AsyncIterator[str]: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

# adapters: OpenAIProvider, ClaudeProvider, GeminiProvider, OllamaProvider
```

Routing rule (config-driven, not hardcoded):

```yaml
routing:
  default: claude-sonnet
  rules:
    - if: "estimated_complexity == low"
      use: gpt-4o-mini
    - if: "estimated_complexity == high or requires_reasoning"
      use: claude-opus
    - if: "workspace.settings.local_only == true"
      use: ollama/llama3
```

`estimated_complexity` starts as a cheap heuristic (question length, presence of multi-part/"compare/why"
keywords) and can later be replaced by a small classifier — the routing config doesn't change either way.

---

## 8. Security & tenancy

- Every query in every service **must** filter by `workspace_id` — enforced via a required parameter on
  repository methods, not left to callers to remember. This is the #1 place multi-tenant RAG apps leak data.
- JWT access tokens (short-lived) + refresh tokens (rotated, stored hashed).
- RBAC checked at the route dependency layer (`require_role("editor")`), never in the frontend only.
- File upload: size limits, MIME sniffing (not just extension trust), virus scan hook (ClamAV) before a
  file is marked `ready` for processing.
- Rate limiting via Redis (sliding window) per user and per workspace.
- Audit log as an append-only table (who did what, when) — separate from `api_usage_log`.

---

## 9. Observability & cost

- Every LLM call and every retrieval call emits a trace (Langfuse or OTel span) tagged with
  `workspace_id`, `conversation_id`, model, token counts, latency, and cache hit/miss.
- `api_usage_log` is the source of truth for the cost dashboard — computed from actual provider responses,
  not estimated.
- Cache layers, in order checked: exact-query response cache → embedding cache → nothing (compute).
  Cache keys are scoped by workspace + model + prompt hash so a cache hit never crosses tenants.

---

## 10. Phased roadmap

**Phase 1 — MVP (this scaffold targets this)**
Auth (email), single workspace per org, PDF/DOCX/TXT/MD upload, fixed+semantic chunking, one embedding
model, pgvector-only search, one LLM provider, streaming chat, citations, basic feedback (👍/👎).

**Phase 2 — Enterprise core**
Multi-workspace, RBAC, collections, hybrid search (BM25 + vector + fusion), re-ranking, OAuth (Google/GitHub),
document versioning, prompt library, admin dashboard, analytics dashboard.

**Phase 3 — Multi-modal & multi-model**
OCR pipeline, website import, YouTube import, audio/video ingestion, multi-model routing, Ollama local
models, observability integration (Langfuse), full caching strategy.

**Phase 4 — Scale & integrations**
Slack/Teams/Jira/Confluence/Notion/SharePoint/Drive/OneDrive connectors, malware scanning, audit logs,
production CI/CD, horizontal scaling of workers, cost-based model routing tuning.

Each phase is additive to the architecture above — no phase requires restructuring the layout in §4.

---

## 11. What's in this scaffold vs. what you build next

Included in the base scaffold (this delivery):
- Full repo layout (§4)
- Docker Compose for Postgres+pgvector, Redis, MinIO, backend, frontend, Celery worker
- FastAPI skeleton: config, DB session, models for the core data model (§5), health check, auth stub,
  documents upload endpoint (saves file + enqueues Celery task), chat endpoint (stub SSE stream)
- Celery worker skeleton with a `process_document` task stub (extract → chunk → embed → store, with
  clear TODOs at each real step)
- Next.js skeleton: layout, a chat page, an upload page, an API client wired to the backend

Not included yet (Phase 2+, intentionally): hybrid search fusion, re-ranking, OAuth, OCR, website/YouTube/
audio/video import, admin dashboard, Langfuse wiring, CI/CD pipeline. The interfaces above are shaped so
each of these is additive.
