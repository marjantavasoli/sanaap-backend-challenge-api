from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet,AuditLogViewSet


router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns=router.urls
