import uuid
import boto3
from botocore.client import Config

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.workers.tasks import process_document_task
from app.models.documents import Document, DocumentStatus

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

# Ensure bucket exists
try:
    s3_client.head_bucket(Bucket=settings.S3_BUCKET)
except Exception:
    try:
        s3_client.create_bucket(Bucket=settings.S3_BUCKET)
    except Exception:
        pass


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

    # Enforce file size limit
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(400, f"File size exceeds the limit of {settings.MAX_UPLOAD_MB}MB")

    document_id = uuid.uuid4()
    storage_path = f"{workspace_id}/{document_id}.{ext}"

    # Stream file to S3
    try:
        s3_client.upload_fileobj(file.file, settings.S3_BUCKET, storage_path)
    except Exception as e:
        raise HTTPException(500, f"Failed to upload to object storage: {str(e)}")

    # Insert Document row
    db_doc = Document(
        id=document_id,
        workspace_id=workspace_id,
        collection_id=collection_id,
        filename=file.filename or "unknown",
        file_type=ext,
        storage_path=storage_path,
        status=DocumentStatus.pending,
        uploaded_by=uuid.UUID("00000000-0000-0000-0000-000000000000"),
    )
    db.add(db_doc)
    await db.commit()

    # Enqueue background processing
    process_document_task.delay(str(document_id))

    return {
        "document_id": document_id,
        "filename": file.filename,
        "status": "pending",
        "message": "File accepted; processing has been queued.",
    }


@router.get("/{document_id}")
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    stmt = select(Document).where(Document.id == document_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.get("")
async def list_documents(workspace_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    stmt = select(Document).where(Document.workspace_id == workspace_id)
    res = await db.execute(stmt)
    docs = res.scalars().all()
    return docs
