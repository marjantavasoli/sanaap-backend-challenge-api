from django.urls import path
from rest_framework.routers import DefaultRouter

from documents.views import AuditLogViewSet, DocumentViewSet
from documents.webhooks import minio_upload_hook

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = router.urls + [
    path("documents/hooks/minio/", minio_upload_hook, name="minio-upload-hook"),
]
