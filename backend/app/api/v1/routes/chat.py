import uuid
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.llm_gateway import get_provider, route_model
from app.services.retrieval import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    workspace_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    question: str
    filters: dict | None = None


@router.post("/stream")
async def stream_chat(payload: ChatRequest):
    """
    Server-Sent Events stream. Frontend consumes this with an SSE/fetch-stream client
    (see frontend/lib/api.ts). Each event is a JSON line: {"type": "token"|"citations"|"done", ...}
    """

    async def event_generator():
        try:
            messages, source_chunks = await answer_question(
                workspace_id=payload.workspace_id,
                question=payload.question,
                filters=payload.filters,
            )
            model_name = route_model(estimated_complexity="low")
            provider = get_provider(model_name)

            async for token in provider.stream_chat(messages):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            citations = [
                {
                    "document_id": c.get("document_id"),
                    "filename": c.get("filename"),
                    "page": c.get("page_number"),
                    "score": c.get("score"),
                }
                for c in source_chunks
            ]
            yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # TODO: persist Message (assistant) + citations once DB layer is wired up

        except NotImplementedError as e:
            # Scaffold state: retrieval/LLM wiring isn't implemented yet.
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
