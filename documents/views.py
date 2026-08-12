from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, viewsets

from common.permissions import DocumentAccessPolicy,IsAdmin
from documents.filters import DocumentFilter
from documents.models import AuditLog, Document
from documents.serializers import DocumentSerializer,AuditLogSerializer
from documents.services import record_document_audit
from documents.ws_notificatins import notify_document_event


@extend_schema(tags=["documents"])
class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD API for documents."""

    serializer_class = DocumentSerializer
    permission_classes = [DocumentAccessPolicy]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = DocumentFilter
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Document.objects.select_related("owner").all()

    def perform_create(self, serializer):
        document = serializer.save()
        record_document_audit(
            self.request.user, AuditLog.Action.CREATE, document=document
        )
        notify_document_event(
            "created",
            document_id=document.id,
            title=document.title,
            status=document.status,
        )

    def perform_update(self, serializer):
        document = serializer.save()
        record_document_audit(
            self.request.user, AuditLog.Action.UPDATE, document=document
        )
        notify_document_event(
            "updated",
            document_id=document.id,
            title=document.title,
            status=document.status,
        )

    def perform_destroy(self, instance):
        document_id, title = instance.id, instance.title
        instance.file.delete(save=False)
        instance.delete()
        record_document_audit(
            self.request.user,
            AuditLog.Action.DELETE,
            document_id=document_id,
            document_title=title,
        )
        notify_document_event("deleted", document_id=document_id, title=title)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        instance = self.get_object()
        record_document_audit(
            request.user, AuditLog.Action.RETRIEVE, document=instance
        )
        return response

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        record_document_audit(request.user, AuditLog.Action.LIST)
        return response


@extend_schema(tags=["audit-logs"])
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to the audit trail. Admins only."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    queryset = AuditLog.objects.select_related("actor").all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["actor", "action", "document_id"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
