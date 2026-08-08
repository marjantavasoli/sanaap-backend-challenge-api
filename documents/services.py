import logging

from django.contrib.auth.models import AnonymousUser

from .models import AuditLog, Document

logger = logging.getLogger(__name__)


def record_document_audit(actor, action, *, document=None, document_id=None, document_title=""):
    """Write a single audit-log entry for a document action."""


    if isinstance(actor, AnonymousUser):
        actor = None

    if actor is not None and not actor.is_authenticated:
        actor = None

    if document is not None:
        document_id = document.id
        document_title = document.title

    try:
        return AuditLog.objects.create(
            actor=actor,
            action=action,
            document_id=document_id,
            document_title=document_title,
        )
    except Exception:
        logger.exception("Failed to write audit log for action=%s", action)
        return None