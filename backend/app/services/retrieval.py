"""
Retrieval pipeline (docs/ARCHITECTURE.md §6). Implemented as discrete, testable
functions now; wrap as LangGraph nodes once the graph is wired up.
"""
import uuid

from app.core.llm_gateway import get_provider


async def embed_query(question: str, provider_name: str | None = None) -> list[float]:
    provider = get_provider(provider_name)
    vectors = await provider.embed([question])
    return vectors[0]


async def vector_search(workspace_id: uuid.UUID, query_embedding: list[float], top_k: int = 10) -> list[dict]:
    """
    pgvector cosine similarity search scoped to workspace_id.
    Queries chunks joined with documents where documents.workspace_id = workspace_id,
    sorted by cosine distance.
    """
    from app.db.session import AsyncSessionLocal
    from app.models.documents import Chunk, Document
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        stmt = (
            select(Chunk, Document.filename)
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.workspace_id == workspace_id)
            .order_by(Chunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        res = await db.execute(stmt)
        results = res.all()

        chunks = []
        for chunk, filename in results:
            chunks.append({
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "content": chunk.content,
                "filename": filename,
                "page_number": chunk.page_number,
                "score": 1.0  # mock score
            })
        return chunks


async def keyword_search(workspace_id: uuid.UUID, query: str, top_k: int = 10) -> list[dict]:
    """Phase 2: Postgres full-text search (ts_rank) scoped to workspace_id, merged via reciprocal rank fusion."""
    raise NotImplementedError("Phase 2 feature - hybrid search not yet implemented")


def apply_metadata_filters(chunks: list[dict], filters: dict | None) -> list[dict]:
    """Filter by file/author/date/tags BEFORE fusion, per docs/ARCHITECTURE.md §6."""
    if not filters:
        return chunks
    # TODO: filter chunks by document metadata matching `filters`
    return chunks


def reciprocal_rank_fusion(*ranked_lists: list[dict], k: int = 60) -> list[dict]:
    """Merge multiple ranked result lists (vector + keyword) into one ranking."""
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            key = item["chunk_id"]
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            items[key] = item
    ordered = sorted(scores, key=scores.get, reverse=True)
    return [items[key] for key in ordered]


async def rerank(query: str, candidates: list[dict], top_n: int = 6) -> list[dict]:
    """Phase 2: cross-encoder or LLM-based re-ranking of fused candidates."""
    return candidates[:top_n]


def build_prompt(question: str, chunks: list[dict], history_summary: str | None = None) -> list[dict]:
    """Assemble the final message list sent to the LLM, with source labels per chunk."""
    context_blocks = "\n\n".join(
        f"[Source {i+1}: {c.get('filename', 'unknown')}"
        f"{', p.' + str(c['page_number']) if c.get('page_number') else ''}]\n{c['content']}"
        for i, c in enumerate(chunks)
    )
    system = (
        "You are a workspace knowledge assistant. Answer ONLY using the provided sources. "
        "If the answer is not in the sources, say so. Cite sources by their [Source N] label."
    )
    messages = [{"role": "system", "content": system}]
    if history_summary:
        messages.append({"role": "system", "content": f"Conversation so far: {history_summary}"})
    messages.append({"role": "user", "content": f"Sources:\n{context_blocks}\n\nQuestion: {question}"})
    return messages


async def answer_question(
    workspace_id: uuid.UUID,
    question: str,
    filters: dict | None = None,
    history_summary: str | None = None,
):
    """
    Full pipeline entry point used by the chat endpoint. Returns (messages_for_llm, source_chunks)
    so the caller can stream the LLM response and attach citations once streaming completes.
    """
    query_embedding = await embed_query(question)
    vector_results = await vector_search(workspace_id, query_embedding)
    filtered = apply_metadata_filters(vector_results, filters)
    reranked = await rerank(question, filtered)
    messages = build_prompt(question, reranked, history_summary)
    return messages, reranked
