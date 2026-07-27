import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.workers.tasks import process_document_task

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()


@router.post("/upload")
async def upload_document(
    workspace_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    collection_id: uuid.UUID | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in settings.ALLOWED_UPLOAD_TYPES:
        raise HTTPException(400, f"File type '.{ext}' not supported")

    # TODO:
    #   1. Stream file to object storage (MinIO/S3), enforcing MAX_UPLOAD_MB
    #   2. Insert Document row with status=pending
    #   3. Enqueue background processing
    document_id = uuid.uuid4()  # placeholder until DB insert is wired up
    process_document_task.delay(str(document_id))

    return {
        "document_id": document_id,
        "filename": file.filename,
        "status": "pending",
        "message": "File accepted; processing has been queued.",
    }


@router.get("/{document_id}")
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # TODO: fetch Document by id, scoped to caller's workspace membership
    raise HTTPException(501, "Not yet implemented")


@router.get("")
async def list_documents(workspace_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # TODO: list documents for workspace_id, paginated
    raise HTTPException(501, "Not yet implemented")
