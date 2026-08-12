import logging

from celery import shared_task

from .models import AuditLog, Document
from .services import record_document_audit

logger = logging.getLogger(__name__)


@shared_task
def process_document(document_id: int) -> None:
    """Finalize a pending document after its object lands in MinIO."""


    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.warning("process_document: document %s not found", document_id)
        return

    # Pull size/content-type from the stored object.
    storage = document.file.storage
    key = document.file.name
    try:
        document.size = storage.size(key)
    except Exception:  # noqa: BLE001 - metadata is best-effort
        logger.exception("process_document: could not read size for %s", key)

    document.status = Document.Status.READY
    document.save(update_fields=["size", "content_type", "status", "updated_at"])

    record_document_audit(
        None, AuditLog.Action.CREATE, document=document
    )