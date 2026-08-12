import logging

from celery import shared_task

from documents.models import Document
from documents.services import DocumentService

logger = logging.getLogger(__name__)


@shared_task
def process_document(document_id: int) -> None:
    """Finalize a pending document after its object lands in MinIO."""
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.warning("process_document: document %s not found", document_id)
        return

    storage = document.file.storage
    key = document.file.name
    try:
        document.size = storage.size(key)
    except Exception:  # noqa: BLE001 - metadata is best-effort
        logger.exception("process_document: could not read size for %s", key)

    document.status = Document.Status.READY
    document.save(update_fields=["size", "content_type", "status", "updated_at"])
    DocumentService().mark_ready(document)
