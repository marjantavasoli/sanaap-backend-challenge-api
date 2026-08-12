import logging

from django.contrib.auth.models import AnonymousUser

from documents.models import AuditLog
from documents.ws_notificatins import notify_document_event

logger = logging.getLogger(__name__)


class DocumentService:
    def handle_created(self, document, actor):
        self._emit(
            AuditLog.Action.CREATE,
            "created",
            document_id=document.id,
            title=document.title,
            status=document.status,
            actor=actor,
        )

    def handle_updated(self, document, actor):
        self._emit(
            AuditLog.Action.UPDATE,
            "updated",
            document_id=document.id,
            title=document.title,
            status=document.status,
            actor=actor,
        )

    def handle_deleted(self, document_id, title, actor):
        self._emit(
            AuditLog.Action.DELETE,
            "deleted",
            document_id=document_id,
            title=title,
            status="",
            actor=actor,
        )

    def record_list_access(self, actor):
        self._record_audit(actor, AuditLog.Action.LIST)

    def record_retrieve_access(self, actor, document):
        self._record_audit(actor, AuditLog.Action.RETRIEVE, document=document)

    def mark_ready(self, document):
        # The upload finished processing; audit as CREATE (finalize) + notify.
        notify_document_event(
            "ready",
            document_id=document.id,
            title=document.title,
            status=document.status,
        )

    def _emit(self, action, event, *, document_id, title, status, actor):
        """
        Record the audit entry and broadcast the notification as a pair.
        """
        self._record_audit(actor, action, document_id=document_id, document_title=title)
        notify_document_event(event, document_id=document_id, title=title, status=status)

    def _record_audit(self, actor, action, *, document=None, document_id=None, document_title=""):
        """
        Write a single audit-log entry. Normalizes the actor and never raises
        """
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
