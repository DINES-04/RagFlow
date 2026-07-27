"""
Document processing pipeline (docs/ARCHITECTURE.md §4 step-by-step).
Called from a Celery task, never from the API request thread directly.
"""
import uuid

from app.core.llm_gateway import get_provider


async def extract_text(storage_path: str, file_type: str) -> str:
    """
    Step 2: extract raw text from the stored file.
    TODO:
      - pdf: pypdf / pdfplumber; if scanned (little/no extractable text), fall back to OCR (Phase 3)
      - docx: python-docx
      - pptx: python-pptx
      - txt/md: read directly
      - csv/xlsx: pandas -> flattened text representation
    """
    raise NotImplementedError(f"Extraction not yet implemented for {file_type}")


def clean_text(raw_text: str) -> str:
    """Step 3: normalize whitespace, strip boilerplate/headers-footers, fix encoding artifacts."""
    return " ".join(raw_text.split())


def chunk_text(text: str, strategy: str = "fixed", chunk_size: int = 800, overlap: int = 120) -> list[dict]:
    """
    Step 4: split into chunks.
      - fixed: sliding window over tokens/characters
      - semantic: split on topic/sentence-embedding similarity shifts
      - parent_child: small child chunks for retrieval, larger parent chunk for context injection
    Returns list of {content, page_number, paragraph_index}.
    """
    if strategy == "fixed":
        words = text.split()
        chunks = []
        step = chunk_size - overlap
        for i in range(0, len(words), step):
            piece = " ".join(words[i : i + chunk_size])
            if piece:
                chunks.append({"content": piece, "page_number": None, "paragraph_index": i // step})
        return chunks
    raise NotImplementedError(f"Chunk strategy '{strategy}' not yet implemented")


async def embed_chunks(chunks: list[dict], provider_name: str | None = None) -> list[dict]:
    """Step 5: generate embeddings for each chunk's content."""
    provider = get_provider(provider_name)
    texts = [c["content"] for c in chunks]
    vectors = await provider.embed(texts)
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


async def process_document(document_id: uuid.UUID) -> None:
    """
    Orchestrates steps 2-8 for a single document. This is the function the Celery
    task calls; kept synchronous-in-spirit (one document, start to finish) so retries
    are simple - if it fails partway, just re-run it.
    """
    # TODO:
    #   1. Load Document row, mark status=processing
    #   2. text = await extract_text(doc.storage_path, doc.file_type)
    #   3. text = clean_text(text)
    #   4. chunks = chunk_text(text, strategy=doc.chunk_strategy)
    #   5. chunks = await embed_chunks(chunks)
    #   6-7. bulk insert Chunk rows (embedding + metadata + source file/page)
    #   8. mark status=ready (or failed, with error captured, on exception)
    raise NotImplementedError("Wire up DB session + steps above")
