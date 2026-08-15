import uuid

from django.conf import settings
from django.db import models

from documents.storages import get_document_storage


def build_document_key(owner_id: int, filename: str) -> str:
    """Single source of truth for a document's object key."""
    return f"documents/{owner_id}/{uuid.uuid4()}/{filename}"


def document_upload_path(instance, filename: str) -> str:
    """Namespace stored objects per owner to keep the bucket organized."""
    return build_document_key(instance.owner_id, filename)


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"

    title = models.CharField(max_length=255)
    file = models.FileField(
        storage=get_document_storage,
        upload_to=document_upload_path,
        max_length=512,
        blank=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    size = models.PositiveBigIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def presigned_url(self) -> str:
        """Short-lived signed URL for downloading this document."""
        return self.file.url if self.file else ""


class AuditLog(models.Model):
    """Immutable record of an action taken against a document."""

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        RETRIEVE = "retrieve", "Retrieve"
        LIST = "list", "List"
        DOWNLOAD = "download", "Download"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=10, choices=Action.choices)
    # Kept as a plain id (not a FK) so a log entry survives the document's
    document_id = models.PositiveBigIntegerField(null=True, blank=True)
    document_title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["document_id"]),
        ]

    def __str__(self) -> str:
        actor = self.actor.username if self.actor else "anonymous"
        return f"{actor} {self.action} doc#{self.document_id}"
