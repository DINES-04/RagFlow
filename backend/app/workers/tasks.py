import asyncio
import uuid

from app.workers.celery_app import celery_app
from app.services.ingestion import process_document


@celery_app.task(name="process_document", bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """Entry point Celery calls; bridges sync Celery worker to the async ingestion service."""
    try:
        asyncio.run(process_document(uuid.UUID(document_id)))
    except Exception as exc:  # noqa: BLE001
        # TODO: mark Document.status = failed with error message once DB layer is wired up
        raise self.retry(exc=exc, countdown=30)


# Phase 3 task stubs - added here so the shape is visible now, implemented later
@celery_app.task(name="crawl_website")
def crawl_website_task(url: str, workspace_id: str):
    raise NotImplementedError("Phase 3: website import not yet implemented")


@celery_app.task(name="import_youtube")
def import_youtube_task(url: str, workspace_id: str):
    raise NotImplementedError("Phase 3: YouTube import not yet implemented")


@celery_app.task(name="transcribe_audio")
def transcribe_audio_task(document_id: str):
    raise NotImplementedError("Phase 3: audio transcription not yet implemented")
