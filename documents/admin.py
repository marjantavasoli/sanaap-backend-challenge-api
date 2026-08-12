from django.contrib import admin

from documents.models import AuditLog, Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("title", "owner__username")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "document_id", "document_title")
    list_filter = ("action", "created_at")
    search_fields = ("actor__username", "document_title")
    readonly_fields = ("actor", "action", "document_id", "document_title", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
