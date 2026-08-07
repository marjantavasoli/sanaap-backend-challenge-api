from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from common.permissions import DocumentAccessPolicy
from .filters import DocumentFilter
from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD API for documents."""


    serializer_class = DocumentSerializer
    permission_classes = [DocumentAccessPolicy]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = DocumentFilter
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # select_related avoids a per-row query for owner.
        return Document.objects.select_related("owner").all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        # Remove the stored object from MinIO before deleting the row.
        instance.file.delete(save=False)
        instance.delete()